"""The Jev judge path, with a scripted fake judge (no network) and a fake HTTP layer for JevJudge itself."""
import io
import json
import urllib.error

import pytest

from syzetetes import judge as J
from syzetetes import schemas
from syzetetes.config import Config, load_config
from syzetetes.engine import Debate
from tests.test_engine import Fake, SRC


class FakeJudge(J.Judge):
    """Answers every question from a script keyed by question name; records what it saw."""
    label = "FakeJudge"

    def __init__(self, status="disputed", lean="codex", dup=0.0, human=0.0, repeats=0.0):
        self.status, self.lean, self.dup, self.human, self.repeats = status, lean, dup, human, repeats
        self.states, self.questions = [], []

    def ask(self, state, questions):
        self.states.append(state); self.questions.append(questions)
        out = {}
        for name, q in questions.items():
            if q["type"] == "choice":
                opts = list(q["criteria"])
                pick = {"status": self.status, "lean": self.lean, "moved": "codex", "crux_kind": "factual"}.get(name, opts[0])
                probs = {o: (0.85 if o == pick else 0.15 / (len(opts) - 1)) for o in opts}
                out[name] = {"type": "choice", "choice": pick, "confidence": 0.8, "probabilities": probs}
            else:
                val = {"human_needed": self.human, "repeats_claude": self.repeats, "repeats_codex": self.repeats}.get(name, self.dup)
                out[name] = {"type": "noul", "noul": val}
        return out


class Scribe(Fake):
    """A fake LLM scribe. Optionally tries to flip statuses, which the engine must ignore."""
    def ask(self, system, prompt, schema, web, what):
        self.calls.append(what)
        if schema is schemas.SCRIBE:
            ids = [line.split()[1] for line in prompt.splitlines() if line.startswith("- K")]
            return {"claims": [{"id": i, "claude_position": f"C on {i}", "codex_position": f"X on {i}", "crux": f"crux {i}"} for i in ids],
                    "round_summary": f"Scribe summary {what}.", "nudge_claude": "Claude: K1 new evidence please",
                    "nudge_codex": "Codex: K1", "human_question": "Decide K1?"}
        return super().ask(system, prompt, schema, web, what)


def _judged_run(tmp_path, judge, max_rounds=2, pause_on=None, checkpoint=None):
    script = {"ledger": lambda r: "disputed"}
    agents = {w: Fake(w, script) for w in ("claude", "codex")}
    agents["referee"] = Scribe("claude", script)
    cfg = Config(out_dir=str(tmp_path), max_rounds=max_rounds, stable_rounds=9, referee="jev",
                 pause_on=pause_on if pause_on is not None else [])
    d = Debate.create("T?", "", cfg, agents=agents, judge=judge, checkpoint=checkpoint)
    d.run()
    return d, agents


def test_judge_decides_statuses_scribe_writes_prose(tmp_path):
    jd = FakeJudge(status="agreed")
    d, agents = _judged_run(tmp_path, jd)
    led = d.state["rounds"][-1]["ledger"]
    assert led["judged_by"] == "FakeJudge"
    assert [c["id"] for c in led["claims"]] == ["K1", "K2"]            # numbered by code, both openings kept
    assert all(c["status"] == "agreed" for c in led["claims"])          # from the judge, not the scribe
    assert led["claims"][0]["claude_position"] == "C on K1"             # from the scribe
    assert led["claims"][0]["crux"] == ""                               # crux only kept for disputed claims
    assert led["settled"] is True and led["needs_human"] is False and led["nudge_claude"] == ""
    j = led["claims"][0]["judge"]
    assert j["status_confidence"] == 0.8 and j["lean"] == "codex" and "status_probabilities" in j
    assert "scribe round 0" in agents["referee"].calls
    # each claim state is small and about this round only
    st = jd.states[-1]
    assert set(st) >= {"topic", "claim", "this_round", "evidence_requests"} and "argument" not in json.dumps(st)
    # every choice was asked twice, forward and reversed
    orders = [list(q["status"]["criteria"]) for q in jd.questions if "status" in q]
    assert orders[0] == list(reversed(orders[1]))
    rep = d.files.report.read_text()
    assert "Jev (jev-latest) judges every claim" in rep and "*Judge: agreed with confidence 0.80" in rep
    assert "Judge verdicts:" in d.files.transcript.read_text()


def test_duplicate_new_claims_merge_and_origin_becomes_both(tmp_path):
    d, _ = _judged_run(tmp_path, FakeJudge(dup=0.95), max_rounds=1)
    led = d.state["rounds"][0]["ledger"]
    assert len(led["claims"]) == 1 and led["claims"][0]["origin"] == "both"


def test_repetition_flags_human_needed_and_low_confidence_pause(tmp_path):
    seen = []
    jd = FakeJudge(status="disputed", human=0.9, repeats=0.8)
    d, _ = _judged_run(tmp_path, jd, max_rounds=1, pause_on=["referee"], checkpoint=lambda q, o: (seen.append(q), "continue")[1])
    led = d.state["rounds"][-1]["ledger"]
    assert led["needs_human"] and led["human_question"] == "Decide K1?"
    assert {f["claim_id"] for f in led["repetition_flags"]} == {"K1", "K2"} and led["nudge_claude"].startswith("Claude")
    assert len(seen) == 2  # referee ask after round 1 + the round-cap prompt

    class Unsure(FakeJudge):
        def ask(self, state, questions):
            out = super().ask(state, questions)
            for v in out.values():
                if v["type"] == "choice":
                    v["confidence"] = 0.3
            return out
    seen.clear()
    d, _ = _judged_run(tmp_path / "u", Unsure(status="disputed"), max_rounds=1, pause_on=["low_confidence"],
                       checkpoint=lambda q, o: (seen.append(q), "continue")[1])
    assert seen and "unsure about" in seen[0]


def test_config_jev_defaults_and_validation(monkeypatch, tmp_path):
    monkeypatch.setattr("syzetetes.config.USER_CONFIG", tmp_path / "absent.toml")
    cfg = load_config({"referee": "jev"})
    assert cfg.referee_model == "haiku" and cfg.scribe == "claude" and cfg.judge_model == "jev-latest"
    assert load_config({"referee": "jev", "referee_model": "sonnet"}).referee_model == "sonnet"
    assert load_config({"pause_on": ["low_confidence"]}).pause_on == ["low_confidence"]
    with pytest.raises(SystemExit):
        load_config({"referee": "gemini"})


def test_jev_http_client(monkeypatch):
    monkeypatch.delenv(J.ENV_KEY, raising=False)
    with pytest.raises(J.JudgeError):
        J.JevJudge()
    sent = {}

    class Resp(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): pass

    def fake_urlopen(req, timeout):
        sent["url"], sent["auth"] = req.full_url, req.get_header("Authorization")
        sent["body"] = json.loads(req.data)
        return Resp(json.dumps({"model": "jev-latest", "answers": {"q": {"type": "noul", "noul": 0.9}},
                                "usage": {"input_tokens": 120, "output_tokens": 2}}).encode())
    monkeypatch.setattr(J.urllib.request, "urlopen", fake_urlopen)
    jd = J.JevJudge(api_key="k1")
    ans = jd.ask({"a": 1}, {"q": J._noul("is it?")})
    assert ans["q"]["noul"] == 0.9 and sent["url"] == J.ENDPOINT and sent["auth"] == "Bearer k1"
    assert sent["body"]["model"] == "jev-latest" and sent["body"]["state"] == {"a": 1} and jd.input_tokens == 120

    calls = {"n": 0}
    def flaky(req, timeout):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError(J.ENDPOINT, 429, "slow down", {}, io.BytesIO(b"rate"))
        return fake_urlopen(req, timeout)
    monkeypatch.setattr(J.urllib.request, "urlopen", flaky)
    monkeypatch.setattr(J.time, "sleep", lambda s: None)
    assert J.JevJudge(api_key="k1").ask({}, {"q": J._noul("x")})["q"]["noul"] == 0.9 and calls["n"] == 2

    def unauthorized(req, timeout):
        raise urllib.error.HTTPError(J.ENDPOINT, 401, "no", {}, io.BytesIO(b""))
    monkeypatch.setattr(J.urllib.request, "urlopen", unauthorized)
    with pytest.raises(J.JudgeError, match="401"):
        J.JevJudge(api_key="bad").ask({}, {"q": J._noul("x")})


def test_merge_choice_averages_orderings():
    a = {"choice": "x", "confidence": 0.6, "probabilities": {"x": 0.6, "y": 0.4}}
    b = {"choice": "y", "confidence": 0.8, "probabilities": {"x": 0.3, "y": 0.7}}
    choice, conf, probs = J._merge_choice(a, b)
    assert choice == "y" and conf == 0.7 and probs == {"x": 0.45, "y": 0.55}
    assert J._trim("a" * 10, 4) == "aaaa […]"


def test_key_from_dotenv(monkeypatch, tmp_path):
    monkeypatch.delenv(J.ENV_KEY, raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env.local").write_text('OTHER=1\nTYPESAFE_API_KEY="abc"\n')
    assert J.JevJudge().api_key == "abc"
