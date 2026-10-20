"""Run folders: a sequential code (D0001, D0002, ...) identifies every debate.

Layout inside the output directory:

    D0001-<topic-slug>/
        D0001.json               state (resumable)
        D0001-01-transcript.md   live log, appended while the debate runs
        D0001-02-report.md       final referenced report
        D0001-03-chat.md         log of grounded Q&A sessions (created by `debate chat`)

Any command that takes a run accepts either the code (`D0001`) or a path to the folder.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

CODE_RE = re.compile(r"^D(\d{4,})(?:-|$)")


@dataclass(frozen=True)
class RunFiles:
    dir: Path
    code: str

    @property
    def state(self) -> Path: return self.dir / f"{self.code}.json"
    @property
    def transcript(self) -> Path: return self.dir / f"{self.code}-01-transcript.md"
    @property
    def report(self) -> Path: return self.dir / f"{self.code}-02-report.md"
    @property
    def chat_log(self) -> Path: return self.dir / f"{self.code}-03-chat.md"


def slugify(topic: str, n: int = 50) -> str:
    return re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:n].rstrip("-") or "debate"


def next_code(out_dir: Path) -> str:
    """D0001 for an empty directory, else one past the highest existing code."""
    highest = 0
    if out_dir.exists():
        for p in out_dir.iterdir():
            m = CODE_RE.match(p.name)
            if m and p.is_dir():
                highest = max(highest, int(m.group(1)))
    return f"D{highest + 1:04d}"


def new_run(out_dir: Path, topic: str) -> RunFiles:
    out_dir.mkdir(parents=True, exist_ok=True)
    code = next_code(out_dir)
    d = out_dir / f"{code}-{slugify(topic)}"
    d.mkdir(exist_ok=False)
    return RunFiles(d, code)


def resolve(ref: str, out_dir: Path) -> RunFiles:
    """`D0001` (any case, number may be unpadded: `d1`) or a path to a run folder."""
    m = re.fullmatch(r"[dD](\d+)", ref.strip())
    if m:
        code = f"D{int(m.group(1)):04d}"
        hits = sorted(p for p in out_dir.glob(f"{code}-*") if p.is_dir()) if out_dir.exists() else []
        if not hits:
            raise FileNotFoundError(f"no run {code} in {out_dir}")
        return RunFiles(hits[0], code)
    p = Path(ref)
    if not p.is_dir():
        raise FileNotFoundError(f"{ref}: not a run code or folder")
    m = CODE_RE.match(p.name)
    if not m:
        raise FileNotFoundError(f"{p.name}: folder is not named like D0001-<slug>")
    return RunFiles(p, f"D{int(m.group(1)):04d}")


def list_runs(out_dir: Path) -> list[RunFiles]:
    if not out_dir.exists():
        return []
    out = []
    for p in sorted(out_dir.iterdir()):
        m = CODE_RE.match(p.name)
        if m and p.is_dir():
            out.append(RunFiles(p, f"D{int(m.group(1)):04d}"))
    return out
