"""Referee + judge: the LLM writes the ledger, Jev rules on every claim. Fake judge, no network."""
import io
import json
import urllib.error

import pytest

from syzetetes import judge as J
from syzetetes.config import Config, load_config
from syzetetes.engine import Debate
from tests.test_engine import Fake


class FakeJudge(J.Judge):
    """Rules `status` on every claim with `conf`; records the states and questions it saw."""
    label = "FakeJudge"

    def __init__(self, status="disputed", conf=0.8, lean="even", lean_conf=0.8, human=0.0):
        self.status, self.conf, self.lean, self.lean_conf, self.human = status, conf, lean, lean_conf, human
        self.states, self.questions = [], []

    def ask(self, state, questions):
        self.states.append(state); self.questions.append(questions)
        out = {}
        for name, q in questions.items():
            if q["type"] == "choice":
                opts = list(q["criteria"])
                pick = {"status": self.status, "lean": self.lean, "moved": "codex", "crux_kind": "factual"}.get(name, opts[0])
                conf = self.lean_conf if name == "lean" else self.conf
                probs = {o: (conf if o == pick else (1 - conf) / (len(opts) - 1)) for o in opts}
                out[name] = {"type": "choice", "choice": pick, "confidence": conf, "probabilities": probs}
            else:
                out[name] = {"type": "noul", "noul": self.human if name == "human_needed" else 0.0}
        return out


def _run(tmp_path, judge, referee_status="disputed", max_rounds=2, pause_on=None, checkpoint=None):
    script = {"ledger": lambda r: referee_status}
    agents = {w: Fake(w, script) for w in ("claude", "codex")}
    agents["referee"] = Fake("claude", script)
    cfg = Config(out_dir=str(tmp_path), max_rounds=max_rounds, stable_rounds=9,
                 pause_on=pause_on if pause_on is not None else [])
    d = Debate.create("T?", "", cfg, agents=agents, judge=judge, checkpoint=checkpoint)
    d.run()
    return d, agents


def test_judge_agrees_attaches_confidence(tmp_path):
    jd = FakeJudge(status="disputed", conf=0.9)
    d, agents = _run(tmp_path, jd)
    led = d.state["rounds"][-1]["ledger"]
    assert led["judged_by"] == "FakeJudge" and led["contested"] == ["K2"]      # K2 is "agreed" in the fake referee
    k1 = led["claims"][0]
    assert k1["status"] == "disputed" and k1["judge"]["contested"] is False and k1["judge"]["status_confidence"] == 0.9
    assert "Judge agrees: disputed with confidence 0.90" in d.files.report.read_text()
    assert "Judge (FakeJudge):" in d.files.transcript.read_text()
    st = jd.states[-1]
    assert set(st) >= {"topic", "claim", "this_round"} and "argument" not in json.dumps(st)
    orders = [list(q["status"]["criteria"]) for q in jd.questions if "status" in q]
    assert orders[0] == list(reversed(orders[1]))                              # asked forward and reversed


def test_confident_disagreement_is_fed_back_to_next_round(tmp_path):
    seen_prompts = []
    jd = FakeJudge(status="conceded", conf=0.85)                                # referee says disputed/agreed
    script = {"ledger": lambda r: "disputed"}
    agents = {w: Fake(w, script) for w in ("claude", "codex")}
    agents["referee"] = Fake("claude", script)
    orig = agents["claude"].ask
    def spy(system, prompt, schema, web, what):
        seen_prompts.append((what, prompt)); return orig(system, prompt, schema, web, what)
    agents["claude"].ask = spy
    ref_orig = agents["referee"].ask
    ref_prompts = []
    def ref_spy(system, prompt, schema, web, what):
        ref_prompts.append(prompt); return ref_orig(system, prompt, schema, web, what)
    agents["referee"].ask = ref_spy
    d = Debate.create("T?", "", Config(out_dir=str(tmp_path), max_rounds=2, stable_rounds=9, pause_on=[]),
                      agents=agents, judge=jd)
    d.run()
    led0 = d.state["rounds"][0]["ledger"]
    assert led0["claims"][0]["judge"]["contested"] and led0["claims"][0]["judge"]["fed_back"]
    assert any("the judge rules conceded (0.85)" in n for n in led0["judge_notes"])
    r1 = next(p for w, p in seen_prompts if w == "round 1")
    assert "judge's rulings after the previous round" in r1 and "K1: the referee recorded it as disputed" in r1
    assert "not binding" in r1
    assert "judge's rulings on your previous ledger" in ref_prompts[1]
    rep = d.files.report.read_text()
    assert "Judge disagrees: rules **conceded**" in rep and "contested" in rep
    assert "fed back to the debaters" in d.files.transcript.read_text()


def test_unconfident_disagreement_is_recorded_but_not_fed_back(tmp_path):
    d, _ = _run(tmp_path, FakeJudge(status="agreed", conf=0.4))
    j = d.state["rounds"][-1]["ledger"]["claims"][0]["judge"]
    assert j["contested"] and not j["fed_back"]
    assert all("K1:" not in n for n in d.state["rounds"][-1]["ledger"]["judge_notes"])


def test_lean_and_human_needed_notes(tmp_path):
    d, _ = _run(tmp_path, FakeJudge(status="disputed", lean="codex", lean_conf=0.9, human=0.9), max_rounds=1)
    notes = d.state["rounds"][-1]["ledger"]["judge_notes"]
    assert any("finds Codex's case stronger" in n and "Claude: produce new evidence" in n for n in notes)
    assert any("cannot settle this without the human" in n for n in notes)


def test_pause_triggers_judge_disagrees_and_low_confidence(tmp_path):
    seen = []
    _run(tmp_path / "a", FakeJudge(status="conceded", conf=0.9), max_rounds=1, pause_on=["judge_disagrees"],
         checkpoint=lambda q, o: (seen.append(q), "continue")[1])
    assert seen and "judge disagrees with the referee" in seen[0]
    seen.clear()
    _run(tmp_path / "b", FakeJudge(status="disputed", conf=0.3), max_rounds=1, pause_on=["low_confidence"],
         checkpoint=lambda q, o: (seen.append(q), "continue")[1])
    assert seen and "unsure about" in seen[0]


def test_no_judge_means_plain_ledger(tmp_path):
    d, _ = _run(tmp_path, None)
    led = d.state["rounds"][-1]["ledger"]
    assert "judged_by" not in led and "judge" not in led["claims"][0]


def test_missing_key_disables_judge_with_warning(tmp_path, monkeypatch, caplog):
    from syzetetes import config as conf
    monkeypatch.setattr(conf, "CREDENTIALS", tmp_path / "none.toml")
    monkeypatch.delenv(J.ENV_KEY, raising=False)
    monkeypatch.chdir(tmp_path)
    import logging
    caplog.set_level(logging.WARNING, logger="syzetetes")
    d = Debate.create("T?", "", Config(out_dir=str(tmp_path), judge="jev"))      # real agents, no key
    assert d.judge is None and "judge disabled" in caplog.text


def test_config_defaults_and_legacy(monkeypatch, tmp_path):
    monkeypatch.setattr("syzetetes.config.USER_CONFIG", tmp_path / "absent.toml")
    cfg = load_config({})
    assert cfg.referee == "claude" and cfg.referee_model == "sonnet" and cfg.judge == "jev"
    legacy = load_config({"referee": "jev", "scribe": "codex", "referee_model": "haiku"})   # old states still load
    assert legacy.referee == "codex" and legacy.judge == "jev" and not hasattr(legacy, "scribe")
    with pytest.raises(SystemExit):
        load_config({"judge": "gemini"})


def test_jev_http_client(monkeypatch, tmp_path):
    monkeypatch.delenv(J.ENV_KEY, raising=False)
    monkeypatch.chdir(tmp_path)
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
    assert sent["body"]["model"] == "jev-latest" and jd.input_tokens == 120

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


def test_key_from_env_then_credentials_file(monkeypatch, tmp_path):
    from syzetetes import config as conf
    creds = tmp_path / "credentials.toml"
    monkeypatch.setattr(conf, "CREDENTIALS", creds)
    monkeypatch.delenv(J.ENV_KEY, raising=False)
    with pytest.raises(J.JudgeError, match="syzetetes key"):
        J.JevJudge()
    path = conf.save_api_key(J.ENV_KEY, 'ab"c')
    assert path == creds and oct(creds.stat().st_mode & 0o777) == "0o600"
    assert J.JevJudge().api_key == 'ab"c' and conf.key_source(J.ENV_KEY) == "credentials.toml"
    conf.save_api_key("OTHER_KEY", "x")                       # merging keeps the first one
    assert conf.api_key(J.ENV_KEY) == 'ab"c' and conf.api_key("OTHER_KEY") == "x"
    monkeypatch.setenv(J.ENV_KEY, "fromenv")
    assert J.JevJudge().api_key == "fromenv" and conf.key_source(J.ENV_KEY) == "env"
    (tmp_path / ".env.local").write_text('TYPESAFE_API_KEY="dotenv"\n')      # no longer read
    monkeypatch.delenv(J.ENV_KEY); monkeypatch.chdir(tmp_path); creds.unlink()
    with pytest.raises(J.JudgeError):
        J.JevJudge()


def test_merge_choice_averages_orderings():
    a = {"choice": "x", "confidence": 0.6, "probabilities": {"x": 0.6, "y": 0.4}}
    b = {"choice": "y", "confidence": 0.8, "probabilities": {"x": 0.3, "y": 0.7}}
    choice, conf, probs = J._merge_choice(a, b)
    assert choice == "y" and conf == 0.7 and probs == {"x": 0.45, "y": 0.55}
