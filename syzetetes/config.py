"""Configuration: built-in defaults, ~/.config/syzetetes/config.toml, then CLI overrides."""
from __future__ import annotations

import dataclasses
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

    # Referee: bookkeeping only. "claude" or "codex".
    referee: str = "claude"
    referee_model: str = "sonnet"
    referee_effort: str = "medium"

    # Debate shape
    max_rounds: int = 8
    stable_rounds: int = 2               # stop when the ledger has not changed status for this many rounds
    research: bool = True
    unattended: bool = False             # alias for pause = "never"
    # When to pause and ask the human (in addition to the referee asking):
    #   never    - run through; deadlocks become agree-to-disagree
    #   referee  - only when the referee asks or the ledger stalls (default)
    #   disputes - after every round that still has a disputed claim
    #   always   - after every round
    pause: str = "referee"
    # Optional expression over round, disputed, open, agreed, conceded, agree_to_disagree, total,
    # unchanged (rounds without a status change). Pauses when true, e.g. "disputed >= 2 and round >= 2".
    pause_when: str = ""

    # Runtime
    timeout_s: int = 1800                # per CLI call
    retries: int = 3
    out_dir: str = "debates"

    def apply_overrides(self, overrides: dict) -> "Config":
        for k, v in overrides.items():
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
    if cfg.unattended:
        cfg.pause = "never"
    if cfg.pause == "never":
        cfg.unattended = True
    if cfg.pause not in ("never", "referee", "disputes", "always"):
        raise SystemExit(f"pause must be never|referee|disputes|always, got {cfg.pause!r}")
    if cfg.referee not in ("claude", "codex"):
        raise ValueError("referee must be 'claude' or 'codex'")
    return cfg
