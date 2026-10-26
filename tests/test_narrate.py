"""Narration: what the terminal shows during a run and what `syzetetes watch` prints. No network."""
import json

from syzetetes import narrate as N
from syzetetes.review import render_review
from tests.test_engine import _run


def test_gist_keeps_the_first_clause_and_drops_labels():
    assert N.gist("C01: Cheaper code does not remove sales costs (S&M is 2x R&D); also more") == \
        "Cheaper code does not remove sales costs"
    assert N.gist("MirrorCode: Claude reimplemented gotree in two days") .startswith("MirrorCode: Claude")
    long = "word " * 40
    assert len(N.gist(long)) <= 81 and N.gist(long).endswith("…")


def test_turn_and_ledger_lines_in_plain_words():
    claims = {"K1": {"id": "K1", "claim": "Pensions can be fixed by reform"}}
    turn = {"responses": [{"claim_id": "K1", "stance": "accept"}], "new_claims": [{"claim": "Robots do care work"}]}
    lines = N.turn_lines("codex", 2, turn, claims)
    assert lines[0] == "Round 2 · Codex" and "agrees" in lines[1] and "Pensions can be fixed" in lines[1]
    assert "new claim" in lines[2] and "\033" not in "".join(lines)
    old = {"claims": [{"id": "K1", "claim": "Pensions can be fixed", "status": "disputed"},
                      {"id": "K2", "claim": "Unchanged one", "status": "agreed"}]}
    new = {"round_summary": "Codex gave ground. More text. Even more.",
           "claims": [{"id": "K1", "claim": "Pensions can be fixed", "status": "agreed",
                       "judge": {"fed_back": True, "status": "disputed", "status_confidence": 0.81}},
                      {"id": "K2", "claim": "Unchanged one", "status": "agreed"}]}
    out = N.ledger_lines(2, old, new)
    assert out[0] == "Referee after round 2: Codex gave ground. More text."
    assert any("disputed → agreed" in x for x in out) and not any("Unchanged" in x for x in out)
    assert any("Judge disagrees on K1: says disputed (0.81)" in x for x in out)


def test_engine_narrates_and_keeps_review_live(tmp_path, monkeypatch):
    said = []
    from syzetetes import engine
    monkeypatch.setattr(engine.progress, "emit", said.append)
    d, _ = _run(tmp_path, {"ledger": lambda r: "disputed" if r < 2 else "conceded"}, {"unattended": True})
    text = "\n".join(said)
    assert "Research done" in text and "Opening · Claude" in text and "Referee after the openings" in text
    assert "Round 1 · Claude" in text and "→" in text
    assert d.files.review.exists()


def test_review_is_live_until_done(tmp_path):
    d, _ = _run(tmp_path, {"ledger": lambda r: "conceded"}, {"unattended": True})
    done = render_review(d.state)
    assert '"phase": "done"' in done                               # the live script returns early
    running = render_review({**d.state, "phase": "rounds"})
    assert '"phase": "rounds"' in running and "location.reload()" in running and 'id="live"' in running


def test_follow_prints_each_round_once_and_stops_when_done(tmp_path):
    d, _ = _run(tmp_path, {"ledger": lambda r: "disputed" if r < 2 else "conceded"}, {"unattended": True})
    final = d.state
    partial = {**final, "phase": "rounds", "rounds": final["rounds"][:2], "synthesis": None}
    states = iter([partial, partial, final])
    printed = []

    def tick(_):                                                   # each "sleep" lands the next saved state
        nxt = next(states, None)
        if nxt is not None:
            d.files.state.write_text(json.dumps(nxt))
            import os
            os.utime(d.files.state, (os.path.getmtime(d.files.state) + len(printed) + 1,) * 2)

    d.files.state.write_text(json.dumps(partial))
    out = N.follow(d.files, emit=printed.append, sleep=tick, interval=0)
    assert out["phase"] == "done"
    assert sum(1 for x in printed if x == "Referee after the openings" or x.startswith("Referee after the openings:")) == 1
    assert any(x.startswith("Verdict:") for x in printed)
