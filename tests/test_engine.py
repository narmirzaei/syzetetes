"""End-to-end run of the engine with scripted fake agents (no CLIs, no network)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from syzetetes import schemas  # noqa: E402
from syzetetes.agents import Agent  # noqa: E402
from syzetetes.config import Config  # noqa: E402
from syzetetes.engine import Debate  # noqa: E402
from syzetetes.report import References, render_report  # noqa: E402

SRC = {"url": "https://example.org/paper", "title": "Example paper", "note": "Shows X."}
SRC2 = {"url": "https://example.org/other/", "title": "", "note": ""}


class Fake(Agent):
    """Returns canned, schema-valid answers; the ledger evolves so termination logic is exercised."""
    name = "fake"

    def __init__(self, who: str, script: dict):
        super().__init__("fake-model", "low", 1, 1)
        self.name = who
        self.script = script
        self.calls: list[str] = []

    def _run(self, system, prompt, schema, web):
        raise NotImplementedError

    def ask(self, system, prompt, schema, web, what):
        self.calls.append(what)
        if schema is schemas.RESEARCH:
            return {"summary": f"Summary by {self.name} (https://example.org/paper).",
                    "findings": [{"finding": "F1", "evidence": "E1", "confidence": "high", "sources": [SRC]}],
                    "contested_points": ["C1"], "open_questions": ["Q1"]}
        if schema is schemas.TURN:
            r = int(what.split()[-1]) if what.startswith("round") else 0
            return {"argument": f"{self.name} argues in {what}. See [paper](https://example.org/paper) and "
                                f"(https://example.org/other/).",
                    "responses": [] if r == 0 else [{"claim_id": "K1", "stance": "maintain", "reasoning": "because",
                                                     "revised_claim": "", "sources": [SRC2]}],
                    "new_claims": [{"claim": f"{self.name} claim", "reasoning": "r", "confidence": "medium",
                                    "sources": [SRC]}] if r == 0 else [],
                    "evidence_requests": [], "nothing_new": r >= self.script.get("nothing_new_at", 99)}
        if schema is schemas.LEDGER:
            r = int(what.split()[-1])
            status = self.script["ledger"](r)
            return {"claims": [{"id": "K1", "claim": "Claude claim", "origin": "claude", "status": status,
                                "claude_position": "yes", "codex_position": "no", "crux": "the crux", "sources": [SRC]},
                               {"id": "K2", "claim": "Codex claim", "origin": "codex", "status": "agreed",
                                "claude_position": "yes", "codex_position": "yes", "crux": "", "sources": []}],
                    "round_summary": f"Round {r} summary.", "repetition_flags": [],
                    "nudge_claude": "", "nudge_codex": "", "needs_human": self.script.get("needs_human", lambda r: False)(r),
                    "human_question": "Decide?", "settled": status not in ("disputed", "open")}
        if schema is schemas.CLOSING:
            return {"statement": f"{self.name} closes.", "changed_my_mind_on": ["a"], "still_unconvinced_on": []}
        if schema is schemas.SYNTHESIS:
            return {"verdict": "The verdict.", "executive_summary": "Summary. https://example.org/paper",
                    "verdicts": [{"claim_id": "K1", "headline": "H1", "explanation": "X1"},
                                 {"claim_id": "K2", "headline": "H2", "explanation": "X2"}],
                    "strongest_case_for": "for", "strongest_case_against": "against",
                    "what_the_author_should_do": "write", "caveats": ["c"]}
        raise AssertionError("unknown schema")


def _run(tmp_path, script, cfg_kw=None, checkpoint=None):
    cfg = Config(**{"out_dir": str(tmp_path), "max_rounds": 4, "stable_rounds": 2, **(cfg_kw or {})})
    agents = {w: Fake(w, script) for w in ("claude", "codex")}
    agents["referee"] = Fake("claude", script)
    d = Debate.create("Should we Test?", "ctx", cfg, agents=agents, checkpoint=checkpoint)
    return d, d.run()


def test_settles_and_reports(tmp_path):
    d, report = _run(tmp_path, {"ledger": lambda r: "disputed" if r < 2 else "conceded"})
    assert "## The referee's verdict\n\nThe verdict." in d.files.report.read_text()
    s = d.state
    assert s["phase"] == "done" and s["stop_reason"] == "All claims settled."
    assert [r["round"] for r in s["rounds"]] == [0, 1, 2]
    assert s["rounds"][1]["first"] == "claude" and s["rounds"][2]["first"] == "codex"
    md = report.read_text()
    assert "## Executive summary" in md and "## Points conceded" in md and "## Points of agreement" in md
    assert "## References" in md and "1. Example paper. <https://example.org/paper>" in md
    assert "[paper](https" not in md and "paper [1]" in md and "[2]" in md
    assert d.files.transcript.exists() and d.files.state.exists()
    assert d.code == "D0001" and d.dir.name.startswith("D0001-")


def test_stall_unattended_stops(tmp_path):
    d, _ = _run(tmp_path, {"ledger": lambda r: "disputed"}, {"unattended": True})
    assert d.state["stop_reason"].startswith("Ledger unchanged")
    assert len(d.state["rounds"]) == 3   # opening + 2 rounds with no change


def test_nothing_new_stops(tmp_path):
    d, _ = _run(tmp_path, {"ledger": lambda r: "disputed", "nothing_new_at": 1}, {"unattended": True})
    assert "nothing new" in d.state["stop_reason"]


def test_human_fact_and_stop(tmp_path):
    replies = iter(["Treat K1 as a value judgement.", "stop"])
    seen = []

    def cp(q, opts):
        seen.append(q)
        return next(replies)

    d, _ = _run(tmp_path, {"ledger": lambda r: "disputed", "needs_human": lambda r: r >= 1}, checkpoint=cp)
    assert len(seen) == 2
    assert d.state["facts"] == ["(after round 1) Treat K1 as a value judgement."]
    assert d.state["stop_reason"] == "Human stopped the debate after round 2."
    assert "Facts set by the human" in d.files.report.read_text()


def test_round_cap_extend(tmp_path):
    replies = iter(["extend 1", "stop"])
    d, _ = _run(tmp_path, {"ledger": lambda r: "disputed" if r % 2 else "open"},
                {"max_rounds": 2}, checkpoint=lambda q, o: next(replies))
    assert d.state["max_rounds"] == 3 and len(d.state["rounds"]) == 4
    assert "human chose to stop" in d.state["stop_reason"]


def test_resume(tmp_path):
    cfg = Config(out_dir=str(tmp_path), max_rounds=3, unattended=True)
    script = {"ledger": lambda r: "disputed" if r < 2 else "agreed"}
    agents = {w: Fake(w, script) for w in ("claude", "codex")}
    agents["referee"] = Fake("claude", script)
    d = Debate.create("Resume me", "", cfg, agents=agents)
    d._research(); d._opening()
    assert d.state["phase"] == "rounds"
    d2 = Debate.resume(d.dir, agents=agents)
    report = d2.run()
    assert d2.state["phase"] == "done" and report.exists()
    assert "Resumed" in d.files.transcript.read_text()


def test_validator():
    good = {"statement": "s", "changed_my_mind_on": [], "still_unconvinced_on": ["x"]}
    assert schemas.validate(good, schemas.CLOSING) == []
    bad = {"statement": 1, "changed_my_mind_on": "no", "extra": True}
    errs = schemas.validate(bad, schemas.CLOSING)
    assert any("still_unconvinced_on: missing" in e for e in errs)
    assert any("statement: expected string" in e for e in errs)
    assert any("extra: unexpected" in e for e in errs)
    assert schemas.validate({"claim_id": "K1", "stance": "nope", "reasoning": "", "revised_claim": "", "sources": []},
                            schemas.TURN["properties"]["responses"]["items"])


def test_references_cite():
    refs = References()
    refs.add({"url": "https://a.com/x", "title": "A"})
    refs.add({"url": "https://a.com/x/longer", "title": "B"})
    text = "see [A](https://a.com/x) and (https://a.com/x/longer) and https://a.com/x."
    assert refs.cite(text) == "see A [1] and [2] and [1]."
    refs2 = References()
    refs2.harvest({"memos": {}, "rounds": [], "closings": {}, "synthesis": None,
                   "extra": None} | {"memos": {"claude": {"summary": "x (https://b.org/p; see also)", "findings": []}}})
    assert refs2.order == ["https://b.org/p"]
    assert refs2.cite("x (https://b.org/p; see also)") == "x ([1]; see also)"


def test_referee_dropped_claim_restored(tmp_path):
    class Dropper(Fake):
        def ask(self, system, prompt, schema, web, what):
            out = super().ask(system, prompt, schema, web, what)
            if schema is schemas.LEDGER and what.endswith("1"):
                out["claims"] = out["claims"][:1]
            return out
    cfg = Config(out_dir=str(tmp_path), max_rounds=1, unattended=True)
    script = {"ledger": lambda r: "disputed"}
    agents = {w: Fake(w, script) for w in ("claude", "codex")}
    agents["referee"] = Dropper("claude", script)
    d = Debate.create("Drop", "", cfg, agents=agents)
    d.run()
    assert {c["id"] for c in d.state["rounds"][1]["ledger"]["claims"]} == {"K1", "K2"}
