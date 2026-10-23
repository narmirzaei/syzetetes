"""Configuration: built-in defaults, the user's config file, then CLI overrides; and the credentials file.

Both live in the XDG config directory ($XDG_CONFIG_HOME, default ~/.config), like gh, pip and poetry:
  config.toml       settings, safe to paste into an issue
  credentials.toml  secrets, mode 0600, never printed
"""
from __future__ import annotations

import dataclasses
import logging
import os
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("syzetetes")

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "syzetetes"
USER_CONFIG = CONFIG_DIR / "config.toml"
CREDENTIALS = CONFIG_DIR / "credentials.toml"
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

    # Referee: an LLM that keeps the ledger. "claude" or "codex".
    referee: str = "claude"
    referee_model: str = "sonnet"
    referee_effort: str = "medium"
    # Judge: rules independently on every claim after every round, with a confidence. "jev" (TypeSafe's
    # decision model, needs $TYPESAFE_API_KEY; skipped with a warning if the key is missing) or "none".
    judge: str = "jev"
    judge_model: str = "jev-latest"      # jev-latest | jev-preview | jev-1.14.0 ...

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
        for k, v in legacy_referee(legacy_pause(overrides)).items():
            if v is not None and hasattr(self, k):
                setattr(self, k, v)
        return self

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


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
    if cfg.referee not in ("claude", "codex"):
        raise SystemExit("referee must be 'claude' or 'codex'")
    if cfg.judge not in ("jev", "none"):
        raise SystemExit("judge must be 'jev' or 'none'")
    return cfg


TRIGGERS = ("referee", "stall", "every_round", "disputes", "agree_to_disagree", "judge_disagrees", "low_confidence")
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


def legacy_referee(overrides: dict) -> dict:
    """Runs made while Jev was the referee: load them as referee = the scribe CLI, judge = jev."""
    if overrides.get("referee") != "jev":
        return {k: v for k, v in overrides.items() if k != "scribe"}
    o = {k: v for k, v in overrides.items() if k != "scribe"}
    o["referee"] = overrides.get("scribe", "claude")
    o["judge"] = "jev"
    return o


# ---------------------------------------------------------------- credentials

def api_key(name: str) -> str:
    """A secret by its environment-variable name: the environment first (12-factor, CI), then the
    credentials file (key in lower case, e.g. typesafe_api_key). Never logged."""
    value = os.environ.get(name, "")
    if value:
        return value
    try:
        if CREDENTIALS.stat().st_mode & 0o077:
            log.warning("%s is readable by other users; run: chmod 600 %s", CREDENTIALS, CREDENTIALS)
        with CREDENTIALS.open("rb") as f:
            return str(tomllib.load(f).get(name.lower(), "") or "")
    except (OSError, tomllib.TOMLDecodeError):
        return ""


def key_source(name: str) -> str:
    """Where a key would come from, for `syzetetes config`: 'env', 'credentials.toml' or ''."""
    if os.environ.get(name):
        return "env"
    return CREDENTIALS.name if api_key(name) else ""


def save_api_key(name: str, value: str) -> Path:
    """Store a secret in the credentials file (created mode 0600; other keys in it are kept)."""
    CREDENTIALS.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    try:
        with CREDENTIALS.open("rb") as f:
            data = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        pass
    data[name.lower()] = value
    body = "".join(f"{k} = {_toml_str(v)}\n" for k, v in data.items())
    fd = os.open(CREDENTIALS, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(body)
    os.chmod(CREDENTIALS, 0o600)
    return CREDENTIALS


def _toml_str(v) -> str:
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'
