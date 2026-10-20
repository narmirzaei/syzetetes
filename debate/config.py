"""Configuration: built-in defaults, ~/.config/debate/config.toml, then CLI overrides."""
from __future__ import annotations

import dataclasses
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

USER_CONFIG = Path.home() / ".config" / "debate" / "config.toml"
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
    unattended: bool = False             # never pause for the human; deadlocks become agree-to-disagree

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
    if cfg.referee not in ("claude", "codex"):
        raise ValueError("referee must be 'claude' or 'codex'")
    return cfg
