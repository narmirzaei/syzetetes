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
MODEL_KEYS = ("claude_model", "claude_effort", "codex_model", "codex_effort", "referee", "referee_model", "referee_effort",
              "scribe", "judge_model")
DEBATE_KEYS = ("max_rounds", "stable_rounds", "research", "pause_on", "out_dir", "timeout_s", "retries")
LEGACY_DEBATE_KEYS = ("pause", "pause_when")
RERUN_KEYS = ("from", "keep_rounds", "redo_openings")


def template(v: dict | None = None) -> str:
    """The commented spec. With `v`, the values are filled in (from the interactive wizard)."""
    c = {**Config().to_dict(), "topic": "", "note": "", "context_files": [], "sources": [], "opinions": [],
         "facts": [], "rerun": None, **(v or {})}
    j = lambda x: json.dumps(x, ensure_ascii=False)
    lst = lambda xs: "[" + ", ".join(j(x) for x in xs) + "]" if len(xs) <= 1 else \
        "[\n" + "".join(f"  {j(x)},\n" for x in xs) + "]"
    rr = c["rerun"]
    rerun = (f'[rerun]\nfrom = {j(rr["from"])}\nkeep_rounds = {int(rr.get("keep_rounds", 0))}\n'
             f'redo_openings = {j(bool(rr.get("redo_openings", False)))}\n') if rr else \
        '# [rerun]\n# from = "D0001"                 # run code or folder\n' \
        '# keep_rounds = 0                # inherit rounds 0..N (0 = openings only)\n' \
        '# redo_openings = false          # true: inherit research only; adding sources implies this\n'
    return f'''# Syzetetes debate spec. Fill it in, then:  syzetetes run {DEFAULT_NAME}
# Every CLI flag has a key here; a flag given on the command line overrides the file.
# Delete any key you do not need: defaults come from ~/.config/syzetetes/config.toml, then built-ins.

# ------------------------------------------------------------------ the question
topic = {j(c["topic"])}                       # required. The question or proposition to debate.

# ------------------------------------------------------------------ starting point (all optional)
note = {j(c["note"])}                        # short inline context, e.g. who you are writing for and why
context_files = {lst(c["context_files"])}               # files whose text is given to both sides as context, e.g. ["notes.md"]
sources = {lst(c["sources"])}                     # URLs or local files both sides must read, cite and check
                                 # e.g. ["https://example.org/paper", "~/papers/jones-2022.txt"]
opinions = {lst(c["opinions"])}                    # your views, NOT binding: the debaters must engage with them, may disagree
                                 # e.g. ["I suspect pensions are the real issue, not fertility."]
facts = {lst(c["facts"])}                       # binding: treated as true for this debate
                                 # e.g. ["Scope is economics only; ignore climate arguments."]

# ------------------------------------------------------------------ models
[models]
claude_model = {j(c["claude_model"])}            # opus | sonnet | haiku | fable | full model id
claude_effort = {j(c["claude_effort"])}           # low | medium | high | xhigh | max
codex_model = {j(c["codex_model"])}       # any model your ChatGPT plan allows
codex_effort = {j(c["codex_effort"])}            # low | medium | high | xhigh | ultra
referee = {j(c["referee"])}                  # jev (default): TypeSafe's decision model judges every claim with confidences
                                 #      (needs $TYPESAFE_API_KEY); the LLM below only writes the prose and the synthesis
                                 # claude | codex: an LLM keeps the whole ledger (use sonnet / medium or better)
referee_model = {j(c["referee_model"])}          # under jev: the scribe's model (haiku is plenty)
referee_effort = {j(c["referee_effort"])}
scribe = {j(c["scribe"])}                # with referee = "jev": claude | codex writes the prose
judge_model = {j(c["judge_model"])}      # with referee = "jev": jev-latest | jev-preview | jev-1.14.0

# ------------------------------------------------------------------ debate shape and human pauses
[debate]
max_rounds = {int(c["max_rounds"])}
stable_rounds = {int(c["stable_rounds"])}                # stop after this many rounds with no status change
research = {j(bool(c["research"]))}                  # false: skip the web-research phase
pause_on = {lst(c["pause_on"])}   # when to stop and ask you (checked after every round); [] = never ask
                                 #   "referee"            the referee cannot resolve something on its own
                                 #   "stall"              nothing changed for stable_rounds rounds (otherwise a stall ends the debate)
                                 #   "every_round"        after every round
                                 #   "disputes"           after every round that still has a disputed claim
                                 #   "agree_to_disagree"  a side wants to agree to disagree on a claim
                                 #   "low_confidence"     (referee = jev) the judge was unsure about a status
                                 #   "round:3"            once, after round 3
                                 #   "custom:disputed >= 2 and round >= 2"   your own condition over the ledger counts
out_dir = {j(c["out_dir"])}              # where run folders go
timeout_s = {int(c["timeout_s"])}                 # seconds per model call
retries = {int(c["retries"])}

# ------------------------------------------------------------------ replay a finished run (optional)
# Derive from an earlier run instead of starting fresh: research (and the kept rounds) are inherited;
# new opinions/facts/sources above are injected at that point and the rest is replayed.
{rerun}'''


PAUSE_MENU = [
    ("referee",           "The referee cannot resolve something on its own (recommended)"),
    ("stall",             "Nothing has changed for a while (otherwise a stall ends the debate)"),
    ("disputes",          "After every round that still has a disputed claim: I tie-break each one"),
    ("agree_to_disagree", "A side wants to agree to disagree on a claim: let me weigh in first"),
    ("low_confidence",    "The judge (Jev) was unsure about a claim's status: let me decide it"),
    ("every_round",       "After every round"),
    ("round:",            "Once, after a specific round"),
    ("custom:",           "A condition of my own over the ledger counts"),
]


def pause_menu(one, say, current: list[str]) -> list[str]:
    """One multi-select question; returns the pause_on list."""
    say("When should the debate stop and ask you? Pick any, comma-separated (e.g. 1,4). 0 = never ask.")
    for i, (_, label) in enumerate(PAUSE_MENU, 1):
        say(f"  {i}. {label}")
    default = ",".join(str(i) for i, (k, _) in enumerate(PAUSE_MENU, 1)
                       if k in current or any(c.startswith(k) for c in current if k.endswith(":"))) or "0"
    valid = {str(i) for i in range(len(PAUSE_MENU) + 1)}
    while True:
        raw = one("Numbers", default)
        picks = [x.strip() for x in str(raw).split(",") if x.strip()]
        if picks and all(x in valid for x in picks):
            break
        say(f"  use numbers 0-{len(PAUSE_MENU)}, separated by commas")
    if "0" in picks:
        return []
    out = []
    for x in picks:
        key = PAUSE_MENU[int(x) - 1][0]
        if key == "round:":
            out.append(f"round:{one('  After which round', 3, cast=int)}")
        elif key == "custom:":
            say("  Counts available after each round: round, disputed, open, agreed, conceded,")
            say("  agree_to_disagree, total, unchanged (rounds in a row with no change). Pauses when true.")
            say('  Example: disputed >= 2 and round >= 2')
            prev = next((c[7:] for c in current if c.startswith("custom:")), "")
            out.append("custom:" + one("  Condition", prev))
        else:
            out.append(key)
    return out


def wizard(ask=input, say=print, defaults: dict | None = None) -> dict:
    """Interactive questionnaire. Enter keeps the default shown in brackets; lists end with a blank line."""
    d = {**Config().to_dict(), **(defaults or {})}
    v: dict = {}

    def one(label, default="", choices=None, required=False, cast=str):
        while True:
            raw = ask(f"{label}{' [' + str(default) + ']' if default != '' else ''}: ").strip()
            if not raw:
                if required and default == "":
                    say("  (required)")
                    continue
                return default
            if choices and raw not in choices:
                say(f"  choose one of: {', '.join(choices)}")
                continue
            try:
                return cast(raw)
            except ValueError:
                say(f"  expected {cast.__name__}")

    def many(label):
        say(f"{label} (one per line, blank line to finish)")
        out = []
        while True:
            raw = ask("  - ").strip()
            if not raw:
                return out
            out.append(raw)

    def yes(label, default):
        return one(label + " (y/n)", "y" if default else "n", choices=["y", "n", "yes", "no"]) in ("y", "yes")

    say("Syzetetes: let's set up a debate. Enter keeps the default in [brackets].\n")
    if yes("Replay a finished run instead of starting fresh?", False):
        v["rerun"] = {"from": one("Run code or folder to replay", required=True),
                      "keep_rounds": one("Inherit rounds 0..N; 0 keeps only the openings", 0, cast=int),
                      "redo_openings": yes("Redo the openings too (keep research only)?", False)}
        say("  New opinions, facts and sources below are injected at that point.\n")
    else:
        v["topic"] = one("Topic: the question or proposition to debate", required=True)
    say("\nStarting point (all optional).")
    v["note"] = one("Short context: who you are, why you ask, who reads the result")
    v["context_files"] = many("Context files (paths)")
    v["sources"] = many("Sources both sides must read and cite (URLs or files)")
    v["opinions"] = many("Your opinions (not binding; the debaters must engage with them)")
    v["facts"] = many("Facts (binding; treated as true for this debate)")
    say("\nModels.")
    v["claude_model"] = one("Claude model (opus | sonnet | haiku | fable | id)", d["claude_model"])
    v["claude_effort"] = one("Claude effort", d["claude_effort"], choices=["low", "medium", "high", "xhigh", "max"])
    v["codex_model"] = one("Codex model", d["codex_model"])
    v["codex_effort"] = one("Codex effort", d["codex_effort"], choices=["low", "medium", "high", "xhigh", "ultra"])
    say("Referee: jev (default; TypeSafe's decision model judges every claim with a confidence, needs")
    say("$TYPESAFE_API_KEY, an LLM scribe writes the prose) or claude / codex (an LLM keeps the whole ledger).")
    v["referee"] = one("Referee", d["referee"], choices=["jev", "claude", "codex"])
    if v["referee"] == "jev":
        v["judge_model"] = one("Jev model", d["judge_model"])
        v["scribe"] = one("Scribe CLI (claude | codex)", d["scribe"], choices=["claude", "codex"])
        v["referee_model"] = one("Scribe model", "haiku")
        v["referee_effort"] = one("Scribe effort", "low")
    else:
        v["referee_model"] = one("Referee model", "sonnet")
        v["referee_effort"] = one("Referee effort", "medium")
    say("\nDebate shape.")
    v["max_rounds"] = one("Max rounds", d["max_rounds"], cast=int)
    v["stable_rounds"] = one("Stop after this many rounds with no status change", d["stable_rounds"], cast=int)
    v["research"] = yes("Web research phase?", d["research"])
    v["pause_on"] = pause_menu(one, say, list(d["pause_on"]))
    v["out_dir"] = one("Output directory", d["out_dir"])
    v["timeout_s"] = one("Seconds per model call", d["timeout_s"], cast=int)
    v["retries"] = one("Retries per call", d["retries"], cast=int)
    return v


def load_spec(path: Path) -> dict:
    with path.open("rb") as f:
        spec = tomllib.load(f)
    unknown = [k for k in spec if k not in INPUT_KEYS and k not in SECTIONS]
    for sec, keys in (("models", MODEL_KEYS), ("debate", DEBATE_KEYS), ("rerun", RERUN_KEYS)):
        unknown += [f"{sec}.{k}" for k in spec.get(sec, {}) if k not in keys and k not in LEGACY_DEBATE_KEYS]
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
    from .config import legacy_pause
    cfg = {**Config().to_dict(), **legacy_pause(state["config"])}   # older runs lack newer keys
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
