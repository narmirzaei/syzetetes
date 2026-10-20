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


def test_init_and_load(tmp_path, capsys):
    p = tmp_path / "s.toml"
    assert main(["init", str(p)]) == 0 and p.exists()
    assert main(["init", str(p)]) == 2                      # refuses to overwrite
    with pytest.raises(SystemExit):
        sp.load_spec(p)                                     # topic empty
    (tmp_path / "ctx.md").write_text("context here")
    p.write_text('topic = "T?"\nnote = "n"\ncontext_files = ["ctx.md"]\nsources = ["https://x", "ctx.md"]\n'
                 'opinions = ["o"]\nfacts = ["f"]\n[models]\nclaude_model = "haiku"\n[debate]\npause = "always"\n')
    s = sp.load_spec(p)
    i = sp.inputs(s, tmp_path)
    assert i["topic"] == "T?" and "context here" in i["context"] and i["sources"][1].endswith("ctx.md")
    assert sp.config_overrides(s) == {"claude_model": "haiku", "pause": "always"}
    p.write_text('topic = "T?"\nbogus = 1\n')
    with pytest.raises(SystemExit):
        sp.load_spec(p)


def test_effective_spec_written_and_reloadable(tmp_path):
    d, _ = _run(tmp_path, {"ledger": lambda r: "conceded"}, {"unattended": True})
    text = d.files.spec.read_text()
    s = tomllib.loads(text)
    assert s["topic"] == "Should we Test?" and s["debate"]["max_rounds"] == 4 and s["models"]["referee"] == "claude"
    assert sp.load_spec(d.files.spec)["topic"] == "Should we Test?"
