"""Orchestration: research → opening → rounds (debater, debater, referee) → closing → synthesis → report.

State is written to <run_dir>/state.json after every step so a run can be resumed. A live
transcript.md is appended as the debate happens so the human can read along.
"""
from __future__ import annotations

import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Callable

from . import prompts, schemas
from .agents import Agent, make_agent
from .config import Config
from .report import render_report

log = logging.getLogger("debate")

# A checkpoint receives (question, options) and returns the human's raw reply.
Checkpoint = Callable[[str, list[str]], str]


def console_checkpoint(question: str, options: list[str]) -> str:
    print("\n" + "=" * 78 + "\nHUMAN CHECKPOINT\n" + "=" * 78)
    print(question)
    print("\nOptions: " + " | ".join(options))
    print("Anything else you type is passed to both debaters as a binding moderator ruling.")
    while True:
        try:
            reply = input("> ").strip()
        except EOFError:
            return "stop"
        if reply:
            return reply


def unattended_checkpoint(question: str, options: list[str]) -> str:
    log.info("unattended: auto-continuing past checkpoint: %s", question[:200])
    return "continue"


class Debate:
    def __init__(self, run_dir: Path, cfg: Config, checkpoint: Checkpoint | None = None,
                 agents: dict[str, Agent] | None = None):
        self.dir = run_dir
        self.cfg = cfg
        self.checkpoint = checkpoint or (unattended_checkpoint if cfg.unattended else console_checkpoint)
        self.state_path = run_dir / "state.json"
        self.transcript = run_dir / "transcript.md"
        if agents is not None:
            self.agents = agents
        else:
            self.agents = {
                "claude": make_agent("claude", cfg.claude_model, cfg.claude_effort, cfg.timeout_s, cfg.retries),
                "codex": make_agent("codex", cfg.codex_model, cfg.codex_effort, cfg.timeout_s, cfg.retries),
                "referee": make_agent(cfg.referee, cfg.referee_model, cfg.referee_effort, cfg.timeout_s, cfg.retries),
            }
        self.state: dict = {}

    # ------------------------------------------------------------ lifecycle

    @classmethod
    def create(cls, topic: str, context: str, cfg: Config, **kw) -> "Debate":
        slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:50] or "debate"
        run_dir = Path(cfg.out_dir) / f"{datetime.now():%Y%m%d-%H%M}-{slug}"
        run_dir.mkdir(parents=True, exist_ok=False)
        d = cls(run_dir, cfg, **kw)
        d.state = {
            "topic": topic, "context": context, "config": cfg.to_dict(),
            "created": datetime.now().isoformat(timespec="seconds"),
            "phase": "research" if cfg.research else "opening",
            "memos": {}, "rounds": [], "rulings": [], "closings": {}, "synthesis": None,
            "stop_reason": "", "max_rounds": cfg.max_rounds,
        }
        d._save()
        d._tx(f"# Debate transcript: {topic}\n\nStarted {d.state['created']}.\n"
              f"Claude: {d.agents['claude'].label}. Codex: {d.agents['codex'].label}. "
              f"Referee: {d.agents['referee'].label}.\n")
        return d

    @classmethod
    def resume(cls, run_dir: Path, **kw) -> "Debate":
        state = json.loads((run_dir / "state.json").read_text())
        cfg = Config().apply_overrides(state["config"])
        d = cls(run_dir, cfg, **kw)
        d.state = state
        d._tx(f"\n> Resumed {datetime.now():%Y-%m-%d %H:%M} at phase '{state['phase']}'.\n")
        return d

    def run(self) -> Path:
        steps = {"research": self._research, "opening": self._opening, "rounds": self._rounds,
                 "closing": self._closing, "synthesis": self._synthesis}
        while self.state["phase"] != "done":
            steps[self.state["phase"]]()
        return self._write_report()

    # ------------------------------------------------------------ phases

    def _research(self):
        topic, ctx = self.state["topic"], self.state["context"]
        log.info("phase: research (both in parallel)")
        memos = self._both(lambda who: self.agents[who].ask(
            prompts.debater_system(who, topic), prompts.research_prompt(topic, ctx),
            schemas.RESEARCH, web=True, what="research"))
        self.state["memos"] = memos
        for who, m in memos.items():
            self._tx(f"\n## Research briefing: {prompts.DISPLAY[who]}\n\n{m['summary']}\n\n" +
                     "\n".join(f"- [{f['confidence']}] {f['finding']} — " + "; ".join(s['url'] for s in f['sources'])
                               for f in m["findings"]) + "\n")
        self._advance("opening")

    def _opening(self):
        topic, ctx, memos = self.state["topic"], self.state["context"], self.state["memos"]
        log.info("phase: opening positions (both in parallel)")
        turns = self._both(lambda who: self.agents[who].ask(
            prompts.debater_system(who, topic), prompts.opening_prompt(topic, ctx, memos),
            schemas.TURN, web=True, what="opening"))
        for who in ("claude", "codex"):
            self._tx(f"\n## Opening: {prompts.DISPLAY[who]}\n\n{turns[who]['argument']}\n")
        ledger = self._referee(None, turns, 0, None)
        self.state["rounds"].append({"round": 0, "first": "both", "turns": turns, "ledger": ledger})
        self._advance("rounds")

    def _rounds(self):
        topic, ctx, memos = self.state["topic"], self.state["context"], self.state["memos"]
        while True:
            r = len(self.state["rounds"])          # next round number (opening was 0)
            prev = self.state["rounds"][-1]
            ledger = prev["ledger"]
            if r > self.state["max_rounds"]:
                if self._finish_or_extend(ledger):
                    continue
                break
            first = "claude" if r % 2 == 1 else "codex"
            second = prompts.OTHER[first]
            log.info("phase: round %d/%d, %s speaks first", r, self.state["max_rounds"], first)
            turns: dict = {}
            for who in (first, second):
                opp = prompts.OTHER[who]
                opp_turn = turns.get(opp) or prev["turns"].get(opp)
                nudge = ledger.get(f"nudge_{who}", "")
                turns[who] = self.agents[who].ask(
                    prompts.debater_system(who, topic),
                    prompts.turn_prompt(who, topic, ctx, memos, ledger, opp_turn, prev["turns"].get(who),
                                        nudge, self.state["rulings"], r, self.state["max_rounds"]),
                    schemas.TURN, web=True, what=f"round {r}")
                self._tx(f"\n## Round {r}: {prompts.DISPLAY[who]}\n\n{turns[who]['argument']}\n")
            prev_ledger = self.state["rounds"][-2]["ledger"] if len(self.state["rounds"]) >= 2 else None
            new_ledger = self._referee(ledger, turns, r, prev_ledger)
            self.state["rounds"].append({"round": r, "first": first, "turns": turns, "ledger": new_ledger})
            self._save()
            if self._should_stop(new_ledger, turns):
                break
        self._advance("closing")

    def _closing(self):
        topic, ledger = self.state["topic"], self.state["rounds"][-1]["ledger"]
        log.info("phase: closing statements")
        closings = self._both(lambda who: self.agents[who].ask(
            prompts.debater_system(who, topic), prompts.closing_prompt(topic, ledger),
            schemas.CLOSING, web=False, what="closing"))
        self.state["closings"] = closings
        for who in ("claude", "codex"):
            self._tx(f"\n## Closing: {prompts.DISPLAY[who]}\n\n{closings[who]['statement']}\n")
        self._advance("synthesis")

    def _synthesis(self):
        s = self.state
        log.info("phase: synthesis")
        s["synthesis"] = self.agents["referee"].ask(
            prompts.synthesis_system(s["topic"]),
            prompts.synthesis_prompt(s["topic"], s["context"], s["rounds"][-1]["ledger"], s["closings"], s["memos"]),
            schemas.SYNTHESIS, web=False, what="synthesis")
        self._advance("done")

    # ------------------------------------------------------------ referee & termination

    def _referee(self, ledger: dict | None, turns: dict, round_no: int, prev_ledger: dict | None) -> dict:
        new = self.agents["referee"].ask(
            prompts.referee_system(self.state["topic"]),
            prompts.referee_prompt(self.state["topic"], ledger, turns, round_no, prev_ledger, self.state["rulings"]),
            schemas.LEDGER, web=False, what=f"referee round {round_no}")
        if ledger:
            # The referee must never drop a claim. Restore any it lost.
            have = {c["id"] for c in new["claims"]}
            for c in ledger["claims"]:
                if c["id"] not in have:
                    log.warning("referee dropped %s; restoring", c["id"])
                    new["claims"].append(c)
        counts = _status_counts(new)
        self._tx(f"\n### Referee after round {round_no}\n\n{new['round_summary']}\n\nStatus: {counts}\n")
        log.info("ledger after round %d: %s", round_no, counts)
        return new

    def _should_stop(self, ledger: dict, turns: dict) -> bool:
        rounds = self.state["rounds"]
        r = rounds[-1]["round"]
        if ledger["settled"]:
            return self._stop("All claims settled.")
        if all(t["nothing_new"] for t in turns.values()):
            return self._stop("Both sides declared they had nothing new to add.")
        if ledger["needs_human"]:
            reply = self.checkpoint(
                f"Round {r}. The referee needs a decision:\n\n{ledger['human_question']}",
                ["continue", "stop", "<type a ruling>"])
            if not self._handle_reply(reply, r):
                return True
        stable = 1
        for a, b in zip(reversed(rounds), list(reversed(rounds))[1:]):
            if _statuses(a["ledger"]) == _statuses(b["ledger"]):
                stable += 1
            else:
                break
        if stable > self.cfg.stable_rounds:
            if self.cfg.unattended:
                return self._stop(f"Ledger unchanged for {stable} rounds.")
            reply = self.checkpoint(
                f"Round {r}. No claim has changed status for {stable} rounds. Remaining disputes:\n"
                + _disputes_md(ledger), ["continue", "stop", "<type a ruling>"])
            if not self._handle_reply(reply, r):
                return True
        return False

    def _finish_or_extend(self, ledger: dict) -> bool:
        """At the round cap. Returns True to keep going (cap raised), False to finish."""
        if ledger["settled"] or self.cfg.unattended:
            self._stop(f"Reached the round cap ({self.state['max_rounds']}).")
            return False
        reply = self.checkpoint(
            f"Round cap of {self.state['max_rounds']} reached with unresolved claims:\n" + _disputes_md(ledger),
            ["stop", "extend <n>", "<type a ruling and extend>"])
        m = re.search(r"extend\s+(\d+)", reply)
        if m:
            self.state["max_rounds"] += int(m.group(1))
            ruling = re.sub(r"extend\s+\d+", "", reply).strip(" ,.;")
            if ruling:
                self._add_ruling(ruling, self.state["max_rounds"])
            self._save()
            return True
        if reply.lower() not in ("stop", "continue"):
            self._add_ruling(reply, self.state["max_rounds"])
            self.state["max_rounds"] += 2
            self._save()
            return True
        self._stop(f"Reached the round cap ({self.state['max_rounds']}); human chose to stop.")
        return False

    def _handle_reply(self, reply: str, round_no: int) -> bool:
        """Returns False if the human stopped the debate."""
        low = reply.strip().lower()
        if low == "stop":
            self._stop(f"Human stopped the debate after round {round_no}.")
            return False
        if low != "continue":
            self._add_ruling(reply.strip(), round_no)
        return True

    def _add_ruling(self, text: str, round_no: int):
        self.state["rulings"].append(f"(after round {round_no}) {text}")
        self._tx(f"\n> **Moderator ruling after round {round_no}:** {text}\n")
        self._save()

    def _stop(self, reason: str) -> bool:
        self.state["stop_reason"] = reason
        self._tx(f"\n> **Debate ended:** {reason}\n")
        log.info("stop: %s", reason)
        return True

    # ------------------------------------------------------------ plumbing

    def _both(self, fn) -> dict:
        with ThreadPoolExecutor(max_workers=2) as ex:
            futs = {who: ex.submit(fn, who) for who in ("claude", "codex")}
            return {who: f.result() for who, f in futs.items()}

    def _advance(self, phase: str):
        self.state["phase"] = phase
        self._save()

    def _save(self):
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, indent=1, ensure_ascii=False))
        tmp.replace(self.state_path)

    def _tx(self, md: str):
        with self.transcript.open("a") as f:
            f.write(md)

    def _write_report(self) -> Path:
        out = self.dir / "report.md"
        out.write_text(render_report(self.state, self.agents))
        log.info("report written: %s", out)
        return out


def _statuses(ledger: dict) -> dict:
    return {c["id"]: c["status"] for c in ledger["claims"]}


def _status_counts(ledger: dict) -> str:
    counts: dict[str, int] = {}
    for c in ledger["claims"]:
        counts[c["status"]] = counts.get(c["status"], 0) + 1
    return ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) or "no claims"


def _disputes_md(ledger: dict) -> str:
    rows = [c for c in ledger["claims"] if c["status"] in ("disputed", "open")]
    return "\n".join(f"- {c['id']}: {c['claim']}\n    crux: {c['crux']}" for c in rows) or "(none)"
