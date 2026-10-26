"""Plain one-line narration of a debate, so you can follow it in the terminal.

Pure functions over the saved state: the live `run` prints them as each step finishes, and
`syzetetes watch` prints them by comparing successive state files. Same lines either way.
No model calls: claim gists are cut from the ledger text.
"""
from __future__ import annotations

import re

from .ui import BOLD, COLORS, DIM, RESET, STATUS_COLORS, clean

NAMES = {"claude": "Claude", "codex": "Codex", "both": "both"}
STANCE = {"accept": "agrees", "maintain": "holds", "revise": "changes", "agree_to_disagree": "agrees to disagree"}
STANCE_COLOR = {"accept": "\033[32m", "maintain": "\033[31m", "revise": "\033[35m", "agree_to_disagree": "\033[33m"}


def gist(text: str, n: int = 80) -> str:
    """The first clause of a claim, cut at a word boundary: enough to recognise it on one line."""
    t = re.sub(r"^\s*[A-Z]{1,2}\d+[:.)]\s*", "", clean(text).strip())        # a leading "C01:" label
    m = re.search(r" \(|; |: |\. |, but | — ", t[25:])                     # cut at the first clause break,
    if m:                                                                    # but keep at least ~25 chars
        t = t[:25 + m.start()]
    t = t.rstrip(".")
    if len(t) > n:
        t = t[:n].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return t


def _paint(color: bool):
    return (lambda code, s: f"{code}{s}{RESET}") if color else (lambda code, s: s)


def _sentences(text: str, k: int = 2) -> str:
    parts = re.split(r"(?<=[.!?])\s+", clean(text).strip())
    return " ".join(parts[:k])


def _who(who: str, c) -> str:
    return c(COLORS.get(who, BOLD), NAMES.get(who, who))


def _status(st: str, c) -> str:
    return c(STATUS_COLORS.get(st, DIM), st.replace("_", " "))


def research_lines(memos: dict, color: bool = False) -> list[str]:
    c = _paint(color)
    out = [c(BOLD, "Research done")]
    for who, m in memos.items():
        out.append(f"  {_who(who, c)} found {len(m.get('findings', []))} points. {gist(m.get('summary', ''), 110)}")
    return out


def turn_lines(who: str, round_no: int, turn: dict, claims: dict[str, dict], color: bool = False) -> list[str]:
    """What one debater did this turn: its stance on each claim, and the claims it added."""
    c = _paint(color)
    head = "Opening" if round_no == 0 else f"Round {round_no}"
    out = [f"{c(BOLD, head)} · {_who(who, c)}" + (c(DIM, "  (nothing new)") if turn.get("nothing_new") else "")]
    for r in turn.get("responses", []):
        cid = clean(r.get("claim_id", ""))
        word = STANCE.get(r.get("stance", ""), r.get("stance", ""))
        text = r.get("revised_claim") or claims.get(cid, {}).get("claim", "")
        out.append(f"  {c(STANCE_COLOR.get(r.get('stance'), ''), f'{word:<19}')}{c(BOLD, cid.ljust(5))} {gist(text)}")
    if round_no == 0:                                  # the referee lists the opening claims with their IDs
        n = len(turn.get("new_claims", []))
        return [out[0] + f": {n} claim{'s' if n != 1 else ''}"]
    for nc in turn.get("new_claims", []):
        out.append(f"  {c(DIM, 'new claim'.ljust(19))}{'':<5} {gist(nc.get('claim', ''))}")
    return out


def ledger_lines(round_no: int, old: dict | None, new: dict, color: bool = False) -> list[str]:
    """The referee's short summary, then only what changed: status moves, new claims, judge disagreements."""
    c = _paint(color)
    before = {x["id"]: x["status"] for x in (old or {}).get("claims", [])}
    head = "Referee after the openings" if round_no == 0 else f"Referee after round {round_no}"
    out = [f"{c(COLORS['referee'], head)}: {_sentences(new.get('round_summary', ''))}"]
    for x in new.get("claims", []):
        cid, st = clean(x["id"]), x["status"]
        if old is None:                                    # after the openings: list every claim once
            out.append(f"  {c(BOLD, f'{cid:<5}')}{_who(x.get('origin', ''), c):<6}  {gist(x['claim'])}  {_status(st, c)}")
        elif cid not in before:
            out.append(f"  {c(BOLD, f'{cid:<5}')}new, {_status(st, c)}  {gist(x['claim'])}")
        elif before[cid] != st:
            out.append(f"  {c(BOLD, f'{cid:<5}')}{_status(before[cid], c)} → {_status(st, c)}  {gist(x['claim'])}")
    for x in new.get("claims", []):
        j = x.get("judge") or {}
        if j.get("fed_back"):                       # confident disagreements: these go back into the debate
            out.append(f"  {c(DIM, 'Judge disagrees on')} {c(BOLD, clean(x['id']))}: says "
                       f"{_status(j['status'], c)} ({j.get('status_confidence', 0):.2f})")
    return out


def end_lines(state: dict, color: bool = False) -> list[str]:
    c = _paint(color)
    verdict = (state.get("synthesis") or {}).get("verdict", "")
    return [f"{c(BOLD, 'Verdict')}: {_sentences(verdict, 3)}"] if verdict else []


def claims_by_id(ledger: dict | None) -> dict[str, dict]:
    return {x["id"]: x for x in (ledger or {}).get("claims", [])}


def state_lines(old: dict | None, new: dict, color: bool = False) -> list[str]:
    """Everything that happened between two saved states (for `syzetetes watch`)."""
    out: list[str] = []
    old = old or {}
    if new.get("memos") and not old.get("memos"):
        out += research_lines(new["memos"], color)
    seen = len(old.get("rounds", []))
    rounds = new.get("rounds", [])
    for i in range(seen, len(rounds)):
        rd = rounds[i]
        prev = rounds[i - 1]["ledger"] if i else None
        known = {**claims_by_id(prev), **claims_by_id(rd["ledger"])}
        order = [rd.get("first")] if rd.get("first") in ("claude", "codex") else ["claude"]
        order += [w for w in ("claude", "codex") if w not in order]
        for who in order:
            if who in rd.get("turns", {}):
                out += turn_lines(who, rd["round"], rd["turns"][who], known, color)
        out += ledger_lines(rd["round"], prev, rd["ledger"], color)
    if new.get("phase") == "done" and old.get("phase") != "done":
        out += end_lines(new, color)
    return out


def follow(files, emit=print, sleep=None, interval: float = 3.0, on_change=None) -> dict:
    """`syzetetes watch`: print what happened each time the run's state file changes, until it is done.
    Read-only on the run; `on_change(state)` lets the caller refresh the review page."""
    import json
    import time
    sleep = sleep or time.sleep
    last, stamp = None, None
    while True:
        try:
            st = files.state.stat().st_mtime
        except FileNotFoundError:
            st = None
        if st is not None and st != stamp:
            try:
                state = json.loads(files.state.read_text())
            except ValueError:                     # caught mid-write; the engine replaces atomically, so retry
                sleep(interval)
                continue
            stamp = st
            for line in state_lines(last, state, color=getattr(emit, "color", False)):
                emit(line)
            if on_change:
                on_change(state)
            last = state
            if state.get("phase") == "done":
                return state
        sleep(interval)
