"""Configuration: built-in defaults, ~/.config/syzetetes/config.toml, then CLI overrides."""
from __future__ import annotations

import dataclasses
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

USER_CONFIG = Path.home() / ".config" / "syzetetes" / "config.toml"
CODEX_USER_CONFIG = Path.home() / ".codex" / "config.toml"


def _codex_default_model() -> str:
    """Use the model the user already picked for Codex, since ChatGPT accounts only allow some models."""
    try:
        with CODEX_USER_CONFIG.open("rb") as f:
            return str(tomllib.load(f).get("model") or "gpt-5-codex")
    except (OSError, tomllib.TOMLDecodeError):
        return "gpt-5-codex"


@dataclass
class Config:
    # Debaters
    claude_model: str = "opus"
    claude_effort: str = "high"          # low | medium | high | xhigh | max
    codex_model: str = field(default_factory=_codex_default_model)
    codex_effort: str = "high"           # low | medium | high | xhigh | ultra (whatever Codex accepts)

    # Referee: bookkeeping only. "claude" or "codex" (an LLM keeps the ledger), or "jev" (TypeSafe's decision
    # model judges every claim; the LLM below only writes the prose and the synthesis; needs $TYPESAFE_API_KEY).
    referee: str = "claude"
    referee_model: str = "sonnet"        # with referee = "jev": the scribe's model (default becomes haiku)
    referee_effort: str = "medium"
    scribe: str = "claude"               # with referee = "jev": which CLI writes the prose, "claude" or "codex"
    judge_model: str = "jev-latest"      # with referee = "jev": jev-latest | jev-preview | jev-1.14.0 ...

    # Debate shape
    max_rounds: int = 8
    stable_rounds: int = 2               # stop when the ledger has not changed status for this many rounds
    research: bool = True
    unattended: bool = False             # alias for pause_on = []
    # Situations in which the debate stops and asks the human (checked after every round):
    #   referee            the referee cannot resolve something on its own
    #   stall              no claim changed status for `stable_rounds` rounds (without this, a stall ends the debate)
    #   every_round        after every round
    #   disputes           after every round that still has a disputed claim
    #   agree_to_disagree  a side wants to agree to disagree on a claim
    #   round:N            once, after round N
    #   custom:EXPR        EXPR over round, disputed, open, agreed, conceded, agree_to_disagree, total, unchanged
    # Empty list: never ask; run through unattended.
    pause_on: list[str] = field(default_factory=lambda: ["referee", "stall"])

    # Runtime
    timeout_s: int = 1800                # per CLI call
    retries: int = 3
    out_dir: str = "debates"

    def apply_overrides(self, overrides: dict) -> "Config":
        for k, v in legacy_pause(overrides).items():
            if v is not None and hasattr(self, k):
                setattr(self, k, v)
        return self

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def _user_sets(key: str) -> bool:
    try:
        with USER_CONFIG.open("rb") as f:
            return key in tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return False


def load_config(overrides: dict | None = None) -> Config:
    cfg = Config()
    if USER_CONFIG.exists():
        with USER_CONFIG.open("rb") as f:
            cfg.apply_overrides(tomllib.load(f))
    if overrides:
        cfg.apply_overrides(overrides)
    cfg.out_dir = str(Path(cfg.out_dir).expanduser())
    if isinstance(cfg.pause_on, str):
        cfg.pause_on = [x.strip() for x in cfg.pause_on.split(",") if x.strip()]
    if cfg.unattended:
        cfg.pause_on = []
    cfg.unattended = not cfg.pause_on
    bad = [t for t in cfg.pause_on if not valid_trigger(t)]
    if bad:
        raise SystemExit(f"pause_on: unknown trigger(s) {bad}; expected one of {', '.join(TRIGGERS)}, round:N, custom:EXPR")
    if cfg.referee not in ("claude", "codex", "jev"):
        raise SystemExit("referee must be 'claude', 'codex' or 'jev'")
    if cfg.scribe not in ("claude", "codex"):
        raise SystemExit("scribe must be 'claude' or 'codex'")
    if cfg.referee == "jev" and "referee_model" not in (overrides or {}) and not _user_sets("referee_model"):
        cfg.referee_model = "haiku"
    return cfg


TRIGGERS = ("referee", "stall", "every_round", "disputes", "agree_to_disagree", "low_confidence")
LEGACY_PAUSE = {"never": [], "referee": ["referee", "stall"], "disputes": ["referee", "stall", "disputes"],
                "always": ["referee", "stall", "every_round"]}


def valid_trigger(t: str) -> bool:
    return t in TRIGGERS or bool(re.fullmatch(r"round:\d+", t)) or t.startswith("custom:")


def legacy_pause(overrides: dict) -> dict:
    """Older specs and state files used `pause` (a preset) and `pause_when` (an expression)."""
    if "pause" not in overrides and "pause_when" not in overrides:
        return overrides
    o = dict(overrides)
    on = list(o.get("pause_on") or LEGACY_PAUSE.get(o.pop("pause", "referee"), ["referee", "stall"]))
    when = o.pop("pause_when", "")
    if when:
        on.append(f"custom:{when}")
    o["pause_on"] = on
    return o
