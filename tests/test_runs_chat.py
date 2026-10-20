from pathlib import Path

import pytest

from syzetetes import chat as chatmod
from syzetetes.chat import Chat
from syzetetes.runs import RunFiles, list_runs, new_run, next_code, resolve


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


def test_cli_parsers_build():
    from syzetetes.cli import _parser
    p = _parser()
    a = p.parse_args(["rerun", "D0001", "--keep-rounds", "2", "--opinion", "x", "--pause-on", "disputes,round:2", "--out", "o"])
    assert (a.run, a.keep_rounds, a.opinion, a.pause_on, a.out_dir) == ("D0001", 2, ["x"], "disputes,round:2", "o")
    a = p.parse_args(["run", "t", "--fact", "r", "--unattended"])
    assert a.fact == ["r"] and a.unattended is True


def test_review_html_embeds_state(tmp_path):
    from syzetetes.review import write_review
    from tests.test_engine import _run
    d, _ = _run(tmp_path, {"ledger": lambda r: "disputed" if r < 2 else "conceded"}, {"unattended": True})
    out = write_review(d.files, d.state)
    html = out.read_text()
    assert out.name == "D0001-04-review.html" and "<!doctype html>" in html
    assert '"topic": "Should we Test?"' in html and '"rounds"' in html and "</script>" in html
    assert "<\\/" in html or "</" not in json_payload(html)


def json_payload(html):
    return html.split("const S = ", 1)[1].split(";\n", 1)[0]
