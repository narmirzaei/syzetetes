"""Terminal progress: a live status line while model calls run, a coloured ledger bar after each
referee pass, and log lines that never collide with the status line.

Active only when stderr is a terminal; otherwise everything degrades to plain log lines, so piping
`2> run.log` keeps working. No dependencies: ANSI escapes and a redraw thread.
"""
from __future__ import annotations

import logging
import sys
import threading
import time

SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
COLORS = {"claude": "\033[38;5;208m", "codex": "\033[38;5;37m", "referee": "\033[38;5;141m", "human": "\033[38;5;205m"}
STATUS_COLORS = {"agreed": "\033[32m", "conceded": "\033[35m", "agree_to_disagree": "\033[33m",
                 "disputed": "\033[31m", "open": "\033[90m"}
STATUS_ORDER = ("agreed", "conceded", "agree_to_disagree", "disputed", "open")
RESET, DIM, BOLD = "\033[0m", "\033[2m", "\033[1m"


def _fmt(secs: float) -> str:
    m, s = divmod(int(secs), 60)
    return f"{m}m{s:02d}s" if m else f"{s}s"


class Progress:
    """Singleton-ish; `ui.progress` is the one the engine and agents talk to."""

    def __init__(self):
        self.enabled = sys.stderr.isatty()
        self.phase = ""
        self.tasks: dict[str, tuple[str, float]] = {}   # label -> (what, started)
        self.lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._paused = False
        self._drawn = False
        self._tick = 0

    # ---------------------------------------------------------------- lifecycle
    def start(self):
        if not self.enabled or self._thread:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        if self._thread:
            self._stop.set()
            self._thread.join(timeout=1)
            self._thread = None
        self._clear()

    def pause(self):
        """Hide the status line while the human types at a checkpoint."""
        with self.lock:
            self._paused = True
            self._clear()

    def resume(self):
        with self.lock:
            self._paused = False

    # ---------------------------------------------------------------- events
    def set_phase(self, text: str):
        with self.lock:
            self.phase = text

    def task_start(self, label: str, what: str):
        with self.lock:
            self.tasks[label] = (what, time.time())

    def task_end(self, label: str):
        with self.lock:
            self.tasks.pop(label, None)

    def ledger(self, round_no: int, counts: dict[str, int]):
        """A one-line coloured bar: ████████░░  agreed 10 · disputed 1 · open 2."""
        total = sum(counts.values()) or 1
        width = 30
        if self.enabled:
            bar = "".join(STATUS_COLORS[k] + "█" * round(width * counts.get(k, 0) / total) for k in STATUS_ORDER) + RESET
            parts = " · ".join(f"{STATUS_COLORS[k]}{counts[k]} {k.replace('_', ' ')}{RESET}"
                               for k in STATUS_ORDER if counts.get(k))
            self.emit(f"{DIM}ledger after round {round_no}{RESET}  {bar}  {parts}")

    def emit(self, line: str):
        """Print a line above the status line."""
        with self.lock:
            self._clear()
            sys.stderr.write(line + "\n")
            sys.stderr.flush()

    # ---------------------------------------------------------------- drawing
    def _line(self) -> str:
        spin = SPINNER[self._tick % len(SPINNER)]
        now = time.time()
        bits = []
        for label, (what, t0) in self.tasks.items():
            who = label.split(" ")[0].lower()
            color = COLORS.get(who, "")
            bits.append(f"{color}{label}{RESET} {what} {DIM}{_fmt(now - t0)}{RESET}")
        body = "  ·  ".join(bits) if bits else f"{DIM}working…{RESET}"
        return f"{BOLD}{spin}{RESET} {self.phase}  {body}" if self.phase else f"{BOLD}{spin}{RESET} {body}"

    def _draw(self):
        sys.stderr.write("\r\033[2K" + self._line())
        sys.stderr.flush()
        self._drawn = True

    def _clear(self):
        if self._drawn:
            sys.stderr.write("\r\033[2K")
            sys.stderr.flush()
            self._drawn = False

    def _loop(self):
        while not self._stop.is_set():
            with self.lock:
                if not self._paused:
                    self._tick += 1
                    self._draw()
            self._stop.wait(0.15)


progress = Progress()


class StatusLineHandler(logging.StreamHandler):
    """Log handler that clears the status line before each record so lines never interleave."""

    def emit(self, record):
        msg = self.format(record)
        if record.levelno >= logging.WARNING and progress.enabled:
            msg = f"\033[33m{msg}{RESET}"
        progress.emit(msg) if progress.enabled else (sys.stderr.write(msg + "\n"), sys.stderr.flush())


def setup_logging():
    h = StatusLineHandler(sys.stderr)
    h.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%H:%M:%S"))
    root = logging.getLogger()
    root.handlers[:] = [h]
    root.setLevel(logging.INFO)
