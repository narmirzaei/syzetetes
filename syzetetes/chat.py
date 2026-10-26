"""`debate chat D0001`: ask questions about a finished debate, answered only from its report.

Grounding: the whole report (verdicts, closings, briefings, full transcript, references) is placed in
the prompt and the model is told to answer from that text alone, or say that the debate does not cover
it. The smallest Claude model is used with effort "low", extended thinking disabled
(MAX_THINKING_TOKENS=0), and no tools, so nothing outside the report can enter the answer.
Note: neither CLI exposes a sampling temperature; this is as deterministic as the CLIs allow.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime

from .agents import Agent, make_agent
from .runs import RunFiles, load_state
from .ui import BOLD, COLORS, DIM, RESET, STATUS_COLORS, clean

CHAT_MODEL = "haiku"
CHAT_EFFORT = "low"
CHAT_ENV = {"MAX_THINKING_TOKENS": "0"}

ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string", "description": "the answer in 1-4 short, plain sentences, using only the document"},
        "covered": {"type": "boolean", "description": "false when the document does not contain enough to answer"},
        "claims": {"type": "array", "description": "every claim ID the answer mentions, each with a plain one-line gist",
                   "items": {"type": "object", "properties": {
                       "id": {"type": "string", "description": "the claim ID exactly as in the document, e.g. K3"},
                       "gist": {"type": "string", "description": "what the claim says, in under 15 everyday words"}},
                       "required": ["id", "gist"], "additionalProperties": False}},
        "evidence": {"type": "array", "items": {"type": "string"},
                     "description": "up to 2 short verbatim excerpts from the document that support the answer"},
    },
    "required": ["answer", "covered", "claims", "evidence"],
    "additionalProperties": False,
}

SYSTEM = """You answer questions about ONE document: the report of a debate between two AI models.
You are a reader of that document, not an expert on the topic.

Hard rules:
- Use only what the document says. No outside knowledge, no inference beyond what the text states.
- If the document does not answer the question, set covered=false and say so plainly. Do not fill in.
- Attribute positions to the side that holds them (Claude, Codex, the referee, or the synthesis).
  Never present a contested claim as a fact.
- When you mention a claim, use its ID exactly as the document does (K1, K2...), and list every
  mentioned claim in `claims` with a one-line gist a non-expert understands.
- Quote evidence verbatim; do not paraphrase inside the evidence list.

How to write:
- Short and simple. One to four sentences, each under 20 words. Lead with the direct answer.
- Everyday words. Replace jargon with what it means: not "population ethics" but "whether more
  people is good in itself"; not "fiscal" but "for government budgets".
- Write the way you would explain it to a smart friend who has not read the report.
- Claim gists: at most 12 words, no jargon, no semicolons.
  Bad:  "Whether extra worthwhile lives count as a benefit is a population-ethics value question"
  Good: "Is having more people good in itself?"
"""


def _prompt(doc: str, history: list[tuple[str, str]], question: str) -> str:
    parts = [f"# Document\n\n{doc}\n\n# Earlier questions in this session\n"]
    if history:
        parts += [f"Q: {q}\nA: {a}\n" for q, a in history]
    else:
        parts.append("(none)\n")
    parts.append(f"# Question\n\n{question}")
    return "\n".join(parts)


def ledger_status(files: RunFiles) -> dict[str, str]:
    """Claim ID -> final status from the saved ledger (the source of truth, not the model)."""
    try:
        rounds = load_state(files).get("rounds", [])
        return {c["id"]: c["status"] for c in rounds[-1]["ledger"]["claims"]} if rounds else {}
    except (OSError, ValueError, KeyError, IndexError):
        return {}


_WHO = re.compile(r"\b(Claude|Codex|the referee|the judge)\b")


def render(out: dict, status: dict[str, str], color: bool) -> str:
    """The answer for a terminal: names and claim IDs highlighted, each mentioned claim explained in one
    line with its ledger status, quotes dimmed. Plain text when `color` is False."""
    c = (lambda code, s: f"{code}{s}{RESET}") if color else (lambda code, s: s)
    ids = {x["id"] for x in out.get("claims", [])} | set(status)
    answer = clean(out["answer"])
    if color:
        answer = _WHO.sub(lambda m: c(COLORS.get(m.group(1).split()[-1].lower(), BOLD), m.group(1)), answer)
        if ids:
            answer = re.sub(r"\b(" + "|".join(map(re.escape, sorted(ids, key=len, reverse=True))) + r")\b",
                            lambda m: c(BOLD, m.group(1)), answer)
    lines = [answer]
    if not out["covered"]:
        lines.append(c("\033[33m", "The debate does not cover this."))
    if out.get("claims"):
        lines.append("")
        for x in out["claims"]:
            st = status.get(x["id"], "")
            tag = c(STATUS_COLORS.get(st, DIM), st.replace("_", " ")) if st else ""
            lines.append(f"  {c(BOLD, clean(x['id']))}  {clean(x['gist'])}" + (f"  {tag}" if tag else ""))
    for e in out.get("evidence", [])[:2]:
        lines.append(c(DIM, f"  “{clean(e)}”"))
    return "\n".join(lines)


def make_chat_agent() -> Agent:
    return make_agent("claude", CHAT_MODEL, CHAT_EFFORT, timeout_s=300, retries=2, extra_env=CHAT_ENV)


class Chat:
    def __init__(self, files: RunFiles, agent: Agent | None = None):
        if not files.report.exists():
            raise FileNotFoundError(f"{files.code} has no report yet ({files.report.name}); finish the run first")
        self.files = files
        self.doc = files.report.read_text()
        self.agent = agent or make_chat_agent()
        self.status = ledger_status(files)
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
            for x in out.get("claims", []):
                f.write(f"\n- **{x['id']}** {x['gist']}" + (f" ({self.status[x['id']]})" if x["id"] in self.status else ""))
            for e in out["evidence"]:
                f.write(f"\n> {e}\n")


def repl(files: RunFiles, agent: Agent | None = None) -> int:
    chat = Chat(files, agent)
    color = sys.stdout.isatty()
    title = chat.doc.splitlines()[0].lstrip("# ")
    print(f"{BOLD}{title}{RESET}" if color else title)
    hint = "Answers come only from this debate's report. Press Enter on an empty line to quit."
    print((f"{DIM}{hint}{RESET}" if color else hint) + "\n")
    while True:
        try:
            q = input(f"{BOLD}?{RESET} " if color else "? ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not q:
            return 0
        out = chat.ask(q)
        print("\n" + render(out, chat.status, color) + "\n")


def one_shot(files: RunFiles, question: str, agent: Agent | None = None) -> int:
    chat = Chat(files, agent)
    out = chat.ask(question)
    if sys.stdout.isatty():
        print(render(out, chat.status, color=True))
    else:
        for x in out.get("claims", []):
            x["status"] = chat.status.get(x["id"], "")
        print(json.dumps(out, indent=1, ensure_ascii=False))
    return 0
