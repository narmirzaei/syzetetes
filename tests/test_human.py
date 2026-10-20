import json

import pytest

from syzetetes.config import Config
from syzetetes.engine import Debate
from tests.test_engine import Fake, _run


def _cp(replies, seen):
    it = iter(replies)
    def cp(q, opts):
        seen.append(q)
        return next(it)
    return cp


def test_opinion_vs_fact_and_prompts(tmp_path):
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
                      checkpoint=_cp(["opinion: actually Y", "fact: K1 is a value judgement; drop it", "stop"], seen))
    d.run()
    assert d.state["opinions"] == ["(before the debate) I think X.", "(after round 1) actually Y"]
    assert d.state["facts"] == ["(after round 2) K1 is a value judgement; drop it"]
    turn = [p for p in prompts if p.startswith("# Task: round 3")][0]
    assert "not binding" in turn and "actually Y" in turn and "binding)" in turn and "value judgement" in turn
    rep = d.files.report.read_text()
    assert "Human's stated opinion" in rep and "Facts set by the human" in rep


def test_pause_on_triggers(tmp_path):
    script = {"ledger": lambda r: "disputed"}
    cases = [  # expected = pauses during rounds + 1 for the round-cap prompt (attended runs)
        (["every_round"], 4), (["disputes"], 4), (["referee", "stall"], 1), (["agree_to_disagree"], 1),
        (["round:2"], 2), (["custom:disputed >= 1 and round >= 2"], 3), (["round:1", "round:3"], 3),
    ]
    for i, (on, expected) in enumerate(cases):
        seen = []
        d, _ = _run(tmp_path / str(i), script, {"pause_on": on, "max_rounds": 3, "stable_rounds": 9},
                    checkpoint=_cp(["continue"] * 10, seen))
        assert len(seen) == expected, (on, seen)


def test_pause_on_empty_is_unattended_and_stall_without_trigger_stops(tmp_path):
    from syzetetes.config import load_config
    assert load_config({"pause_on": []}).unattended is True
    assert load_config({"unattended": True}).pause_on == []
    assert load_config({"pause": "disputes", "pause_when": "round == 2"}).pause_on == \
        ["referee", "stall", "disputes", "custom:round == 2"]          # legacy keys still work
    with pytest.raises(SystemExit):
        load_config({"pause_on": ["bogus"]})
    seen = []
    d, _ = _run(tmp_path / "s", {"ledger": lambda r: "disputed"},
                {"pause_on": ["referee"], "max_rounds": 6, "stable_rounds": 1}, checkpoint=_cp(["continue"] * 9, seen))
    assert d.state["stop_reason"].startswith("Ledger unchanged") and seen == []


def test_rerun_inherits_and_adds(tmp_path):
    script = {"ledger": lambda r: "disputed" if r < 2 else "conceded"}
    d1, _ = _run(tmp_path, script, {"unattended": True})
    assert d1.code == "D0001" and len(d1.state["rounds"]) >= 3
    agents = {w: Fake(w, script) for w in ("claude", "codex")}
    agents["referee"] = Fake("claude", script)
    d2 = Debate.derive(d1.dir, {"out_dir": str(tmp_path)}, keep_rounds=1, facts=["Assume Z."],
                       opinions=["My take."], agents=agents)
    assert d2.code == "D0002" and d2.state["phase"] == "rounds"
    assert d2.state["memos"] == d1.state["memos"]
    assert [r["round"] for r in d2.state["rounds"]] == [0, 1]
    assert d2.state["facts"] == ["(after round 1, added retrospectively) Assume Z."]
    assert "D0001" in d2.state["derived_from"]
    d2.run()
    assert d2.state["phase"] == "done" and "Derived from" in d2.files.report.read_text()
    d3 = Debate.derive("D0001", {"out_dir": str(tmp_path)}, redo_openings=True, agents=agents)
    assert d3.state["phase"] == "opening" and d3.state["rounds"] == []


def test_sources_flow_to_prompts_and_report(tmp_path):
    from syzetetes.runs import load_sources
    f = tmp_path / "paper.txt"; f.write_text("Pensions depend on the worker ratio.")
    sources = load_sources(["https://example.org/x", str(f)])
    assert sources[0]["kind"] == "url" and sources[1]["kind"] == "file" and "worker ratio" in sources[1]["text"]
    script = {"ledger": lambda r: "conceded"}
    prompts = []
    agents = {w: Fake(w, script) for w in ("claude", "codex")}
    agents["referee"] = Fake("claude", script)
    orig = agents["codex"].ask
    def spy(system, prompt, schema, web, what):
        prompts.append(prompt); return orig(system, prompt, schema, web, what)
    agents["codex"].ask = spy
    d = Debate.create("T?", "ctx", Config(out_dir=str(tmp_path), unattended=True), sources=sources, agents=agents)
    d.run()
    research = [p for p in prompts if p.startswith("# Task: independent research")][0]
    assert "Starting point" in research and "S1: https://example.org/x" in research and "worker ratio" in research
    rep = d.files.report.read_text()
    assert "starting sources" in rep and "paper.txt" in rep
    # rerun with a new source redoes research
    d2 = Debate.derive(d.dir, {"out_dir": str(tmp_path)}, keep_rounds=1, agents=agents,
                       sources=load_sources(["https://example.org/y"]))
    assert d2.state["phase"] == "research" and d2.state["memos"] == {} and len(d2.state["sources"]) == 3
