"""`debate chat D0001`: ask questions about a finished debate, answered only from its report.

Grounding: the whole report (verdicts, closings, briefings, full transcript, references) is placed in
the prompt and the model is told to answer from that text alone, or say that the debate does not cover
it. The smallest Claude model is used with effort "low", extended thinking disabled
(MAX_THINKING_TOKENS=0), and no tools, so nothing outside the report can enter the answer.
Note: neither CLI exposes a sampling temperature; this is as deterministic as the CLIs allow.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime

from .agents import Agent, make_agent
from .ui import clean
from .runs import RunFiles

CHAT_MODEL = "haiku"
CHAT_EFFORT = "low"
CHAT_ENV = {"MAX_THINKING_TOKENS": "0"}

ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string", "description": "the answer, in plain prose, with no information from outside the document"},
        "covered": {"type": "boolean", "description": "false when the document does not contain enough to answer"},
        "evidence": {"type": "array", "items": {"type": "string"},
                     "description": "short verbatim excerpts from the document that support the answer (0-5)"},
    },
    "required": ["answer", "covered", "evidence"],
    "additionalProperties": False,
}

SYSTEM = """You answer questions about ONE document: the report of a debate between two AI models.
You are a reader of that document, not an expert on the topic.

Hard rules:
- Use only what the document says. No outside knowledge, no inference beyond what the text states.
- If the document does not answer the question, set covered=false and say so plainly. Do not fill in.
- Attribute positions to the side that holds them (Claude, Codex, the referee, or the synthesis).
  Never present a contested claim as a fact.
- Refer to claims by their IDs and sources by their [n] markers exactly as the document does.
- Quote evidence verbatim; do not paraphrase inside the evidence list.
- Be concise."""


def _prompt(doc: str, history: list[tuple[str, str]], question: str) -> str:
    parts = [f"# Document\n\n{doc}\n\n# Earlier questions in this session\n"]
    if history:
        parts += [f"Q: {q}\nA: {a}\n" for q, a in history]
    else:
        parts.append("(none)\n")
    parts.append(f"# Question\n\n{question}")
    return "\n".join(parts)


def make_chat_agent() -> Agent:
    return make_agent("claude", CHAT_MODEL, CHAT_EFFORT, timeout_s=300, retries=2, extra_env=CHAT_ENV)


class Chat:
    def __init__(self, files: RunFiles, agent: Agent | None = None):
        if not files.report.exists():
            raise FileNotFoundError(f"{files.code} has no report yet ({files.report.name}); finish the run first")
        self.files = files
        self.doc = files.report.read_text()
        self.agent = agent or make_chat_agent()
        self.history: list[tuple[str, str]] = []

    def ask(self, question: str) -> dict:
        out = self.agent.ask(SYSTEM, _prompt(self.doc, self.history, question), ANSWER_SCHEMA,
                             web=False, what="chat")
        self.history.append((question, out["answer"]))
        self._log(question, out)
        return out

    def _log(self, question: str, out: dict):
        new = not self.files.chat_log.exists()
        with self.files.chat_log.open("a") as f:
            if new:
                f.write(f"# {self.files.code} — Q&A log\n\nGrounded on `{self.files.report.name}`; "
                        f"model {self.agent.label}, thinking disabled, no tools.\n")
            f.write(f"\n## {datetime.now():%Y-%m-%d %H:%M} — {question}\n\n{out['answer']}\n")
            if not out["covered"]:
                f.write("\n*Not covered by the debate.*\n")
            for e in out["evidence"]:
                f.write(f"\n> {e}\n")


def repl(files: RunFiles, agent: Agent | None = None) -> int:
    chat = Chat(files, agent)
    print(f"{files.code}: {chat.doc.splitlines()[0].lstrip('# ')}")
    print(f"Answers come only from {files.report.name}. Empty line or Ctrl-D to quit.\n")
    while True:
        try:
            q = input("? ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not q:
            return 0
        out = chat.ask(q)
        print()
        print(clean(out["answer"]))
        if not out["covered"]:
            print("\n(The debate does not cover this.)")
        for e in out["evidence"]:
            print(f"\n  > {clean(e)}")
        print()


def one_shot(files: RunFiles, question: str, agent: Agent | None = None) -> int:
    out = Chat(files, agent).ask(question)
    print(json.dumps(out, indent=1, ensure_ascii=False) if not sys.stdout.isatty() else clean(out["answer"]))
    return 0
