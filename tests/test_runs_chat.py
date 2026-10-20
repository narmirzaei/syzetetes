from pathlib import Path

import pytest

from debate import chat as chatmod
from debate.chat import Chat
from debate.runs import RunFiles, list_runs, new_run, next_code, resolve


def test_codes_are_sequential_and_resolvable(tmp_path):
    a = new_run(tmp_path, "First topic!")
    b = new_run(tmp_path, "Second")
    assert (a.code, b.code) == ("D0001", "D0002")
    assert a.dir.name == "D0001-first-topic"
    assert a.state.name == "D0001.json"
    assert a.transcript.name == "D0001-01-transcript.md"
    assert a.report.name == "D0001-02-report.md"
    assert a.chat_log.name == "D0003-03-chat.md".replace("D0003", "D0001")
    assert next_code(tmp_path) == "D0003"
    assert resolve("D0002", tmp_path).dir == b.dir
    assert resolve("d2", tmp_path).dir == b.dir
    assert resolve(str(a.dir), tmp_path).code == "D0001"
    assert [r.code for r in list_runs(tmp_path)] == ["D0001", "D0002"]
    with pytest.raises(FileNotFoundError):
        resolve("D0009", tmp_path)


class _GroundedFake:
    """Records what it was asked and answers from the document only when the question's word is in it."""
    label = "fake"

    def __init__(self):
        self.calls = []

    def ask(self, system, prompt, schema, web, what):
        self.calls.append((system, prompt, web))
        doc = prompt.split("# Document\n\n", 1)[1].split("\n\n# Earlier questions", 1)[0]
        q = prompt.rsplit("# Question\n\n", 1)[1]
        hit = next((w for w in q.split() if w in doc), None)
        return ({"answer": f"The report mentions {hit}.", "covered": True, "evidence": [hit]} if hit
                else {"answer": "Not in the report.", "covered": False, "evidence": []})


def test_chat_grounds_on_report_and_logs(tmp_path):
    files = new_run(tmp_path, "t")
    files.report.write_text("# D0001 — t\n\nClaude says pensions are fixable [1].\n")
    fake = _GroundedFake()
    c = Chat(files, fake)
    out = c.ask("what about pensions")
    assert out["covered"] and "pensions" in out["answer"]
    out2 = c.ask("what about zebras")
    assert not out2["covered"]
    system, prompt, web = fake.calls[1]
    assert web is False and "only" in system.lower()
    assert "Q: what about pensions" in prompt           # session history is carried
    log = files.chat_log.read_text()
    assert "what about pensions" in log and "Not covered" in log


def test_chat_agent_is_smallest_model_no_thinking():
    a = chatmod.make_chat_agent()
    assert a.model == "haiku" and a.effort == "low"
    assert a.extra_env == {"MAX_THINKING_TOKENS": "0"}


def test_chat_refuses_without_report(tmp_path):
    with pytest.raises(FileNotFoundError):
        Chat(new_run(tmp_path, "x"), _GroundedFake())
