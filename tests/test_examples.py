"""Every example spec must load under the current schema and reference only files that exist, and every
example the README links to must exist. This is what keeps examples from going stale."""
import re
from pathlib import Path

import pytest

from syzetetes import spec as sp

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = sorted((ROOT / "examples").glob("*.toml"))


@pytest.mark.parametrize("path", EXAMPLES, ids=[p.name for p in EXAMPLES])
def test_example_loads_and_its_files_exist(path):
    spec = sp.load_spec(path)                       # unknown keys or a missing topic raise
    inp = sp.inputs(spec, path.parent)              # context_files are read here: a missing one raises
    assert spec.get("topic") or spec.get("rerun")
    for src in inp["sources"]:
        if not src.startswith(("http://", "https://")):
            assert Path(src).is_file(), f"{path.name}: source file missing: {src}"
    from syzetetes.config import load_config
    load_config(sp.config_overrides(spec))         # model/debate keys validate (referee, judge, pause_on...)


def test_readme_links_to_existing_examples_and_every_example_is_linked():
    readme = (ROOT / "README.md").read_text()
    linked = set(re.findall(r"examples/([\w.-]+\.toml)", readme))
    existing = {p.name for p in EXAMPLES}
    assert linked <= existing, f"README links to missing examples: {linked - existing}"
    assert existing <= linked, f"examples not mentioned in README: {existing - linked}"


def test_example_report_is_current_format():
    rep = (ROOT / "example-report.md").read_text()
    assert rep.startswith("# D0"), "example-report.md should come from a coded run"
    assert "| Judge |" in rep and "The referee's verdict" in rep, "example-report.md predates the judge/verdict"
