"""Subprocess wrappers around the Claude Code CLI and the Codex CLI.

Both run on the user's subscriptions (no API keys). Each call is single-shot:
the full context is passed in the prompt, nothing depends on CLI session state.
Both CLIs are isolated from the user's personal settings so that MCP servers,
plugins, hooks and CLAUDE.md/AGENTS.md files do not leak into the debate.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
from abc import ABC, abstractmethod
from pathlib import Path

from .schemas import SchemaError, validate

log = logging.getLogger("debate")


class AgentError(RuntimeError):
    pass


class Agent(ABC):
    name: str          # "claude" | "codex"
    model: str
    effort: str

    def __init__(self, model: str, effort: str, timeout_s: int = 1800, retries: int = 3,
                 extra_env: dict[str, str] | None = None):
        self.model, self.effort, self.timeout_s, self.retries = model, effort, timeout_s, retries
        self.extra_env = extra_env or {}

    @property
    def label(self) -> str:
        return f"{self.name.capitalize()} ({self.model}, {self.effort})"

    def ask(self, system: str, prompt: str, schema: dict, web: bool, what: str) -> dict:
        """Ask once, validate, retry with the validation errors fed back. Raises AgentError when exhausted."""
        last_err = ""
        for attempt in range(1, self.retries + 1):
            t0 = time.time()
            p = prompt if not last_err else (
                f"{prompt}\n\n# Correction\nYour previous answer was rejected because it did not match the "
                f"required output schema:\n{last_err}\nAnswer again, fully, matching the schema exactly."
            )
            try:
                out = self._run(system, p, schema, web)
                errs = validate(out, schema)
                if errs:
                    raise SchemaError("; ".join(errs[:10]))
                log.info("%s · %s · ok in %.0fs", self.label, what, time.time() - t0)
                return out
            except (SchemaError, AgentError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
                last_err = str(e)[:2000]
                log.warning("%s · %s · attempt %d/%d failed after %.0fs: %s",
                            self.label, what, attempt, self.retries, time.time() - t0, last_err[:300])
        raise AgentError(f"{self.label} failed {what} after {self.retries} attempts: {last_err}")

    @abstractmethod
    def _run(self, system: str, prompt: str, schema: dict, web: bool) -> dict: ...


class ClaudeAgent(Agent):
    name = "claude"

    def _run(self, system: str, prompt: str, schema: dict, web: bool) -> dict:
        exe = shutil.which("claude")
        if not exe:
            raise AgentError("claude CLI not found on PATH")
        tools = "WebSearch,WebFetch" if web else ""
        cmd = [
            exe, "-p",
            "--model", self.model, "--effort", self.effort,
            "--output-format", "json", "--json-schema", json.dumps(schema),
            "--system-prompt", system,
            "--tools", tools,
            "--no-session-persistence", "--setting-sources", "", "--strict-mcp-config", "--disable-slash-commands",
        ]
        if web:
            cmd += ["--allowedTools", "WebSearch", "WebFetch"]
        env = {**os.environ, **self.extra_env}
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=self.timeout_s, env=env)
        if r.returncode != 0:
            raise AgentError(f"claude exit {r.returncode}: {_claude_error(r.stdout, r.stderr)}")
        data = json.loads(r.stdout)
        if data.get("is_error"):
            raise AgentError(f"claude reported error: {str(data.get('result'))[:1500]}")
        so = data.get("structured_output")
        if so is None:
            # Occasionally the model answers in text; try to parse it before giving up.
            so = json.loads(data.get("result") or "null")
        if not isinstance(so, dict):
            raise AgentError("claude returned no structured output")
        return so


def _claude_error(stdout: str, stderr: str) -> str:
    """Pull the informative fields out of a failed `claude -p` run instead of the tail of the usage blob."""
    try:
        d = json.loads(stdout)
        keys = ("subtype", "stop_reason", "terminal_reason", "result", "error", "errors")
        found = {k: d[k] for k in keys if k in d}
        if found:
            return json.dumps(found)[:1500]
    except (json.JSONDecodeError, TypeError):
        pass
    return (stderr.strip() or stdout.strip())[:1500]


class CodexAgent(Agent):
    name = "codex"

    def _run(self, system: str, prompt: str, schema: dict, web: bool) -> dict:
        exe = shutil.which("codex")
        if not exe:
            raise AgentError("codex CLI not found on PATH")
        # Codex has no system-prompt flag; the role block goes at the top of the prompt.
        full = f"# Your role and rules\n\n{system}\n\n---\n\n{prompt}"
        with tempfile.TemporaryDirectory(prefix="debate-codex-") as td:
            schema_path = Path(td) / "schema.json"
            out_path = Path(td) / "last.txt"
            schema_path.write_text(json.dumps(schema))
            cmd = [
                exe, "exec",
                "--skip-git-repo-check", "--ephemeral", "--ignore-user-config",
                "-s", "read-only", "-C", td, "--color", "never",
                "-m", self.model, "-c", f"model_reasoning_effort={json.dumps(self.effort)}",
                "-c", f"web_search={'\"live\"' if web else '\"disabled\"'}",
                "--output-schema", str(schema_path), "-o", str(out_path),
                "-",
            ]
            r = subprocess.run(cmd, input=full, capture_output=True, text=True, timeout=self.timeout_s)
            if r.returncode != 0 or not out_path.exists():
                raise AgentError(f"codex exit {r.returncode}: {(r.stderr or r.stdout)[-1500:]}")
            text = out_path.read_text().strip()
        data = json.loads(text)
        if not isinstance(data, dict):
            raise AgentError("codex returned no JSON object")
        return data


def make_agent(kind: str, model: str, effort: str, timeout_s: int, retries: int,
               extra_env: dict[str, str] | None = None) -> Agent:
    cls = {"claude": ClaudeAgent, "codex": CodexAgent}[kind]
    return cls(model, effort, timeout_s, retries, extra_env=extra_env)
