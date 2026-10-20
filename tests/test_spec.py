import tomllib
from pathlib import Path

import pytest

from syzetetes import spec as sp
from syzetetes.cli import main
from tests.test_engine import _run


def test_template_parses_and_lists_every_config_key(tmp_path):
    t = sp.template()
    d = tomllib.loads(t)
    assert d["topic"] == "" and set(d["models"]) == set(sp.MODEL_KEYS) and set(d["debate"]) == set(sp.DEBATE_KEYS)
    from syzetetes.config import Config
    import dataclasses
    cfg_fields = {f.name for f in dataclasses.fields(Config)} - {"unattended"}
    assert cfg_fields == set(sp.MODEL_KEYS) | set(sp.DEBATE_KEYS)


def test_init_allocates_run_folder(tmp_path, capsys):
    out = tmp_path / "runs"
    assert main(["init", "--out", str(out)]) == 0
    assert (out / "D0001-untitled" / "D0001-00-spec.toml").exists()
    assert main(["init", "Is X true?", "--out", str(out)]) == 0
    spec = out / "D0002-is-x-true" / "D0002-00-spec.toml"
    assert spec.exists() and sp.load_spec(spec)["topic"] == "Is X true?"
    assert "syzetetes run D0002" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        sp.load_spec(out / "D0001-untitled" / "D0001-00-spec.toml")   # topic empty


def test_run_code_uses_init_folder_and_renames(tmp_path, monkeypatch):
    from syzetetes.config import Config
    from syzetetes.engine import Debate
    from syzetetes.runs import resolve
    from tests.test_engine import Fake
    out = tmp_path / "runs"
    main(["init", "--out", str(out)])
    files = resolve("D0001", out)
    files.spec.write_text('topic = "Renamed topic"\n[debate]\nmax_rounds = 1\n')
    script = {"ledger": lambda r: "conceded"}
    agents = {w: Fake(w, script) for w in ("claude", "codex")}; agents["referee"] = Fake("claude", script)
    d = Debate.create("Renamed topic", "", Config(out_dir=str(out), unattended=True, max_rounds=1),
                      files=files, agents=agents)
    assert d.code == "D0001" and d.dir.name == "D0001-renamed-topic" and not (out / "D0001-untitled").exists()
    d.run()
    assert d.files.report.exists()
    assert main(["run", "D0001", "--out", str(out)]) == 2        # already ran


def test_load_spec_inputs(tmp_path):
    p = tmp_path / "s.toml"
    (tmp_path / "ctx.md").write_text("context here")
    p.write_text('topic = "T?"\nnote = "n"\ncontext_files = ["ctx.md"]\nsources = ["https://x", "ctx.md"]\n'
                 'opinions = ["o"]\nfacts = ["f"]\n[models]\nclaude_model = "haiku"\n[debate]\npause_on = ["every_round"]\n')
    s = sp.load_spec(p)
    i = sp.inputs(s, tmp_path)
    assert i["topic"] == "T?" and "context here" in i["context"] and i["sources"][1].endswith("ctx.md")
    assert sp.config_overrides(s) == {"claude_model": "haiku", "pause_on": ["every_round"]}
    p.write_text('topic = "T?"\nbogus = 1\n')
    with pytest.raises(SystemExit):
        sp.load_spec(p)


def test_effective_spec_written_and_reloadable(tmp_path):
    d, _ = _run(tmp_path, {"ledger": lambda r: "conceded"}, {"unattended": True})
    text = d.files.spec.read_text()
    s = tomllib.loads(text)
    assert s["topic"] == "Should we Test?" and s["debate"]["max_rounds"] == 4 and s["models"]["referee"] == "claude"
    assert sp.load_spec(d.files.spec)["topic"] == "Should we Test?"


def test_wizard_fills_template(tmp_path):
    answers = iter([
        "n",                                  # replay? no
        "Is X true?",                         # topic
        "for engineers",                      # note
        "",                                   # context files: none
        "https://a", "notes.md", "",          # sources
        "I think yes", "",                    # opinions
        "",                                   # facts
        "sonnet", "bogus", "low",             # claude model, bad effort then ok
        "", "medium", "codex", "", "",        # codex model default, effort, referee, model, effort
        "3", "", "n",                         # rounds, stable, research
        "3,6", "2", "", "", "",               # pause menu: disputes + once after round 2; out_dir, timeout, retries
    ])
    said = []
    v = sp.wizard(ask=lambda _: next(answers), say=said.append)
    text = sp.template(v)
    d = tomllib.loads(text)
    assert d["topic"] == "Is X true?" and d["sources"] == ["https://a", "notes.md"] and d["opinions"] == ["I think yes"]
    assert d["models"]["claude_model"] == "sonnet" and d["models"]["claude_effort"] == "low"
    assert d["models"]["codex_effort"] == "medium" and d["models"]["referee"] == "codex"
    assert d["debate"]["max_rounds"] == 3 and d["debate"]["research"] is False
    assert d["debate"]["pause_on"] == ["disputes", "round:2"]
    assert "rerun" not in d
    assert any("choose one of" in m for m in said)
    p = tmp_path / "w.toml"; p.write_text(text)
    assert sp.load_spec(p)["topic"] == "Is X true?"


def test_wizard_rerun_branch():
    answers = iter(["y", "D0001", "2", "n", "", "", "", "", "a fact", "",
                    "", "", "", "", "", "", "", "", "", "y", "", "", "", ""])
    v = sp.wizard(ask=lambda _: next(answers), say=lambda *_: None)
    d = tomllib.loads(sp.template(v))
    assert d["rerun"] == {"from": "D0001", "keep_rounds": 2, "redo_openings": False} and d["facts"] == ["a fact"]
    assert d["topic"] == ""


def test_wizard_pause_menu_zero_means_never_and_rejects_bad(tmp_path):
    said = []
    answers = iter(["9", "0"])
    out = sp.pause_menu(lambda label, default="", **k: next(answers), said.append, ["referee", "stall"])
    assert out == [] and any("use numbers" in m for m in said)
    answers = iter(["7", "open >= 1"])
    assert sp.pause_menu(lambda label, default="", **k: next(answers), said.append, []) == ["custom:open >= 1"]
