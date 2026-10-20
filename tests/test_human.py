import json

from debate.config import Config
from debate.engine import Debate
from tests.test_engine import Fake, _run


def _cp(replies, seen):
    it = iter(replies)
    def cp(q, opts):
        seen.append(q)
        return next(it)
    return cp


def test_opinion_vs_ruling_and_prompts(tmp_path):
    seen, prompts = [], []
    script = {"ledger": lambda r: "disputed", "needs_human": lambda r: r in (1, 2)}
    cfg = Config(out_dir=str(tmp_path), max_rounds=3, stable_rounds=5)
    agents = {w: Fake(w, script) for w in ("claude", "codex")}
    agents["referee"] = Fake("claude", script)
    orig = agents["claude"].ask
    def spy(system, prompt, schema, web, what):
        prompts.append(prompt); return orig(system, prompt, schema, web, what)
    agents["claude"].ask = spy
    d = Debate.create("T?", "", cfg, agents=agents, opinions=["I think X."],
                      checkpoint=_cp(["opinion: actually Y", "K1 is a value judgement; drop it", "stop"], seen))
    d.run()
    assert d.state["opinions"] == ["(before the debate) I think X.", "(after round 1) actually Y"]
    assert d.state["rulings"] == ["(after round 2) K1 is a value judgement; drop it"]
    turn = [p for p in prompts if p.startswith("# Task: round 3")][0]
    assert "not binding" in turn and "actually Y" in turn and "binding)" in turn and "value judgement" in turn
    rep = d.files.report.read_text()
    assert "Human's stated opinion" in rep and "Moderator rulings" in rep


def test_pause_policies(tmp_path):
    script = {"ledger": lambda r: "disputed"}
    for pause, when, expected in [("always", "", 4), ("disputes", "", 4), ("referee", "", 1),  # +1: round-cap prompt
                                  ("referee", "disputed >= 1 and round >= 2", 3)]:
        seen = []
        d, _ = _run(tmp_path / (pause + when.replace(" ", "")), script,
                    {"pause": pause, "pause_when": when, "max_rounds": 3, "stable_rounds": 9, "unattended": False},
                    checkpoint=_cp(["continue"] * 10, seen))
        assert len(seen) == expected, (pause, when, seen)
    assert Config(pause="never").unattended is False  # only load_config normalises; engine respects cfg.unattended


def test_rerun_inherits_and_adds(tmp_path):
    script = {"ledger": lambda r: "disputed" if r < 2 else "conceded"}
    d1, _ = _run(tmp_path, script, {"unattended": True})
    assert d1.code == "D0001" and len(d1.state["rounds"]) >= 3
    agents = {w: Fake(w, script) for w in ("claude", "codex")}
    agents["referee"] = Fake("claude", script)
    d2 = Debate.derive(d1.dir, {"out_dir": str(tmp_path)}, keep_rounds=1, rulings=["Assume Z."],
                       opinions=["My take."], agents=agents)
    assert d2.code == "D0002" and d2.state["phase"] == "rounds"
    assert d2.state["memos"] == d1.state["memos"]
    assert [r["round"] for r in d2.state["rounds"]] == [0, 1]
    assert d2.state["rulings"] == ["(after round 1, added retrospectively) Assume Z."]
    assert "D0001" in d2.state["derived_from"]
    d2.run()
    assert d2.state["phase"] == "done" and "Derived from" in d2.files.report.read_text()
    d3 = Debate.derive("D0001", {"out_dir": str(tmp_path)}, redo_openings=True, agents=agents)
    assert d3.state["phase"] == "opening" and d3.state["rounds"] == []
