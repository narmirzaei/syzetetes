"""Debate spec files: everything a run needs, in one TOML file.

    syzetetes init                 # writes syzetetes.toml, a commented template to fill in
    syzetetes run syzetetes.toml   # runs it; any CLI flag still overrides the file

TOML rather than YAML because Python reads it with no third-party dependency and it supports comments.
The effective spec is saved into the run folder as <code>-00-spec.toml so a run can be reproduced.
"""
from __future__ import annotations

import json
import tomllib
from pathlib import Path

from .config import Config

DEFAULT_NAME = "syzetetes.toml"

# Keys allowed at the top level of a spec, besides the sections below.
INPUT_KEYS = ("topic", "note", "context_files", "sources", "opinions", "facts")
SECTIONS = ("models", "debate", "rerun")
MODEL_KEYS = ("claude_model", "claude_effort", "codex_model", "codex_effort", "referee", "referee_model", "referee_effort")
DEBATE_KEYS = ("max_rounds", "stable_rounds", "research", "pause", "pause_when", "out_dir", "timeout_s", "retries")
RERUN_KEYS = ("from", "keep_rounds", "redo_openings")


def template() -> str:
    c = Config()
    return f'''# Syzetetes debate spec. Fill it in, then:  syzetetes run {DEFAULT_NAME}
# Every CLI flag has a key here; a flag given on the command line overrides the file.
# Delete any key you do not need: defaults come from ~/.config/syzetetes/config.toml, then built-ins.

# ------------------------------------------------------------------ the question
topic = ""                       # required. The question or proposition to debate.

# ------------------------------------------------------------------ starting point (all optional)
note = ""                        # short inline context, e.g. who you are writing for and why
context_files = []               # files whose text is given to both sides as context, e.g. ["notes.md"]
sources = []                     # URLs or local files both sides must read, cite and check
                                 # e.g. ["https://example.org/paper", "~/papers/jones-2022.txt"]
opinions = []                    # your views, NOT binding: the debaters must engage with them, may disagree
                                 # e.g. ["I suspect pensions are the real issue, not fertility."]
facts = []                       # binding: treated as true for this debate
                                 # e.g. ["Scope is economics only; ignore climate arguments."]

# ------------------------------------------------------------------ models
[models]
claude_model = "{c.claude_model}"            # opus | sonnet | haiku | fable | full model id
claude_effort = "{c.claude_effort}"           # low | medium | high | xhigh | max
codex_model = "{c.codex_model}"       # any model your ChatGPT plan allows
codex_effort = "{c.codex_effort}"            # low | medium | high | xhigh | ultra
referee = "{c.referee}"               # claude | codex: which CLI keeps the ledger and writes the synthesis
referee_model = "{c.referee_model}"
referee_effort = "{c.referee_effort}"

# ------------------------------------------------------------------ debate shape and human pauses
[debate]
max_rounds = {c.max_rounds}
stable_rounds = {c.stable_rounds}                # stop after this many rounds with no status change
research = {json.dumps(c.research)}                  # false: skip the web-research phase
pause = "{c.pause}"               # never | referee | disputes | always
                                 #   never    run through; deadlocks become agree-to-disagree
                                 #   referee  only when the referee asks or the ledger stalls
                                 #   disputes after every round that still has a disputed claim
                                 #   always   after every round
pause_when = ""                  # extra condition, e.g. "disputed >= 2 and round >= 2"
                                 # names: round, disputed, open, agreed, conceded, agree_to_disagree, total, unchanged
out_dir = "{c.out_dir}"              # where run folders go
timeout_s = {c.timeout_s}                 # seconds per model call
retries = {c.retries}

# ------------------------------------------------------------------ replay a finished run (optional)
# Uncomment to derive from an earlier run instead of starting fresh: research (and the kept rounds)
# are inherited; new opinions/facts/sources above are injected at that point and the rest is replayed.
# [rerun]
# from = "D0001"                 # run code or folder
# keep_rounds = 0                # inherit rounds 0..N (0 = openings only)
# redo_openings = false          # true: inherit research only; adding sources implies this
'''


def load_spec(path: Path) -> dict:
    with path.open("rb") as f:
        spec = tomllib.load(f)
    unknown = [k for k in spec if k not in INPUT_KEYS and k not in SECTIONS]
    for sec, keys in (("models", MODEL_KEYS), ("debate", DEBATE_KEYS), ("rerun", RERUN_KEYS)):
        unknown += [f"{sec}.{k}" for k in spec.get(sec, {}) if k not in keys]
    if unknown:
        raise SystemExit(f"{path}: unknown key(s): {', '.join(unknown)}")
    if "rerun" not in spec and not spec.get("topic", "").strip():
        raise SystemExit(f"{path}: 'topic' is required (or a [rerun] section)")
    return spec


def config_overrides(spec: dict) -> dict:
    """The [models] and [debate] sections flattened to Config field names."""
    return {**spec.get("models", {}), **spec.get("debate", {})}


def inputs(spec: dict, base: Path) -> dict:
    """topic, context, sources, opinions, facts; file paths resolve relative to the spec file."""
    parts = [spec.get("note", "")]
    for f in spec.get("context_files", []):
        parts.append((base / Path(f).expanduser()).read_text())
    return {
        "topic": spec.get("topic", ""),
        "context": "\n\n".join(p.strip() for p in parts if p and p.strip()),
        "sources": [s if s.startswith(("http://", "https://")) else str(base / Path(s).expanduser())
                    for s in spec.get("sources", [])],
        "opinions": list(spec.get("opinions", [])),
        "facts": list(spec.get("facts", [])),
    }


def effective_spec(state: dict) -> str:
    """Render a run's state back into a spec file that reproduces it."""
    cfg = {**Config().to_dict(), **state["config"]}          # older runs lack newer keys
    strip = lambda xs: [x.split(") ", 1)[1] if x.startswith("(") and ") " in x else x for x in xs]

    def kv(k, v):
        return f"{k} = {json.dumps(v, ensure_ascii=False)}"

    lines = [f"# Effective spec for {state.get('code', '')} — reproduce with: syzetetes run <this file>",
             kv("topic", state["topic"]), kv("note", state.get("context", "")),
             kv("sources", [s["ref"] for s in state.get("sources", [])]),
             kv("opinions", strip(state.get("opinions", []))), kv("facts", strip(state.get("facts", []))),
             "", "[models]"] + [kv(k, cfg[k]) for k in MODEL_KEYS] + \
            ["", "[debate]"] + [kv(k, cfg[k]) for k in DEBATE_KEYS]
    if state.get("derived_from"):
        lines += ["", f"# derived from {state['derived_from']}"]
    return "\n".join(lines) + "\n"
