"""Orchestration: research → opening → rounds (debater, debater, referee) → closing → synthesis → report.

State is written to <run_dir>/<code>.json after every step so a run can be resumed. A live
<code>-01-transcript.md is appended as the debate happens so the human can read along (see runs.py).
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
from . import judge as judging
from .report import render_report
from .review import write_review
from .runs import RunFiles, load_state, new_run, rename_slug, resolve
from .spec import effective_spec
from .ui import progress

log = logging.getLogger("syzetetes")

# A checkpoint receives (question, options) and returns the human's raw reply.
Checkpoint = Callable[[str, list[str]], str]


def console_checkpoint(question: str, options: list[str]) -> str:
    progress.pause()
    try:
        return _console_checkpoint(question, options)
    finally:
        progress.resume()


def _console_checkpoint(question: str, options: list[str]) -> str:
    print("\n" + "=" * 78 + "\nHUMAN CHECKPOINT\n" + "=" * 78)
    print(question)
    print("\nOptions: " + " | ".join(options))
    print("  opinion: <text>   your view; the debaters must weigh it but may disagree")
    print("  fact: <text>      binding; both debaters treat it as true from here on")
    print("  <anything else>   also taken as a binding fact")
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
    def __init__(self, files: RunFiles, cfg: Config, checkpoint: Checkpoint | None = None,
                 agents: dict[str, Agent] | None = None, judge: "judging.Judge | None" = None):
        self.files = files
        self.dir = files.dir
        self.code = files.code
        self.cfg = cfg
        if cfg.unattended:
            cfg.pause_on = []
        cfg.unattended = not cfg.pause_on
        self.checkpoint = checkpoint or (unattended_checkpoint if cfg.unattended else console_checkpoint)
        self.state_path = files.state
        self.transcript = files.transcript
        if agents is not None:
            self.agents = agents
        else:
            llm_ref = cfg.scribe if cfg.referee == "jev" else cfg.referee
            self.agents = {
                "claude": make_agent("claude", cfg.claude_model, cfg.claude_effort, cfg.timeout_s, cfg.retries),
                "codex": make_agent("codex", cfg.codex_model, cfg.codex_effort, cfg.timeout_s, cfg.retries),
                "referee": make_agent(llm_ref, cfg.referee_model, cfg.referee_effort, cfg.timeout_s, cfg.retries),
            }
        self.judge = judge if judge is not None else (judging.make_judge("jev", cfg.judge_model) if cfg.referee == "jev" else None)
        self.state: dict = {}

    # ------------------------------------------------------------ lifecycle

    @classmethod
    def create(cls, topic: str, context: str, cfg: Config, facts: list[str] = (), opinions: list[str] = (),
               sources: list[dict] = (), files: RunFiles | None = None, **kw) -> "Debate":
        """`files`: a folder already allocated by `syzetetes init`; otherwise a new code is taken."""
        files = rename_slug(files, topic) if files else new_run(Path(cfg.out_dir), topic)
        d = cls(files, cfg, **kw)
        d.state = {
            "code": files.code, "topic": topic, "context": context, "sources": list(sources), "config": cfg.to_dict(),
            "created": datetime.now().isoformat(timespec="seconds"),
            "phase": "research" if cfg.research else "opening",
            "memos": {}, "rounds": [], "facts": [], "opinions": [], "closings": {}, "synthesis": None,
            "stop_reason": "", "max_rounds": cfg.max_rounds,
        }
        for text in facts:
            d.state["facts"].append(f"(before the debate) {text}")
        for text in opinions:
            d.state["opinions"].append(f"(before the debate) {text}")
        d._save()
        files.spec.write_text(effective_spec(d.state))
        d._tx(f"# {files.code} — Debate transcript: {topic}\n\nStarted {d.state['created']}.\n"
              f"Claude: {d.agents['claude'].label}. Codex: {d.agents['codex'].label}. "
              f"Referee: {d.agents['referee'].label}.\n")
        if sources:
            d._tx("\nStarting sources: " + ", ".join(x["ref"] for x in sources) + "\n")
        for r in d.state["facts"]:
            d._tx(f"\n> **Fact set by the human (binding):** {r}\n")
        for o in d.state["opinions"]:
            d._tx(f"\n> **Human opinion (not binding):** {o}\n")
        return d

    @classmethod
    def derive(cls, src: str | Path, cfg_overrides: dict, keep_rounds: int = 0, redo_openings: bool = False,
               facts: list[str] = (), opinions: list[str] = (), sources: list[dict] = (),
               files: RunFiles | None = None, **kw) -> "Debate":
        """A new run that inherits a finished run's research (and the first `keep_rounds` rounds) and
        re-runs the rest, so the human can add an opinion or a fact retrospectively. Adding sources
        redoes the research too, since the briefings must start from them."""
        src_files = resolve(str(src), Path(Config().apply_overrides(cfg_overrides).out_dir))
        old = load_state(src_files)
        cfg = Config().apply_overrides(old["config"]).apply_overrides(cfg_overrides)
        files = rename_slug(files, old["topic"]) if files else new_run(Path(cfg.out_dir), old["topic"])
        d = cls(files, cfg, **kw)
        if sources:
            redo_openings = True
        kept = [] if redo_openings else [r for r in old["rounds"] if r["round"] <= keep_rounds]
        all_sources = list(old.get("sources", [])) + list(sources)
        d.state = {
            "code": files.code, "topic": old["topic"], "context": old["context"], "config": cfg.to_dict(),
            "created": datetime.now().isoformat(timespec="seconds"),
            "sources": all_sources,
            "derived_from": f"{old.get('code') or src_files.code} ("
                            + ("new sources, research redone" if sources else "kept research")
                            + ("" if redo_openings else f" and rounds 0-{keep_rounds}") + ")",
            "phase": "research" if sources else ("opening" if redo_openings else "rounds"),
            "memos": {} if sources else old["memos"], "rounds": kept, "closings": {}, "synthesis": None,
            "facts": list(old.get("facts", old.get("rulings", []))), "opinions": list(old.get("opinions", [])),
            "stop_reason": "", "max_rounds": cfg.max_rounds,
        }
        at = "before the debate" if redo_openings else f"after round {keep_rounds}"
        for text in facts:
            d.state["facts"].append(f"({at}, added retrospectively) {text}")
        for text in opinions:
            d.state["opinions"].append(f"({at}, added retrospectively) {text}")
        d._save()
        files.spec.write_text(effective_spec(d.state))
        d._tx(f"# {files.code} — Debate transcript: {old['topic']}\n\nStarted {d.state['created']}, "
              f"derived from {d.state['derived_from']}; see that run's transcript for the inherited part.\n")
        for r in d.state["facts"]:
            d._tx(f"\n> **Fact set by the human (binding):** {r}\n")
        for o in d.state["opinions"]:
            d._tx(f"\n> **Human opinion (not binding):** {o}\n")
        return d

    @classmethod
    def resume(cls, ref: str | Path, **kw) -> "Debate":
        files = resolve(str(ref), Path(Config().out_dir))
        state = load_state(files)
        cfg = Config().apply_overrides(state["config"])
        d = cls(files, cfg, **kw)
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
        progress.set_phase("Research")
        memos = self._both(lambda who: self.agents[who].ask(
            prompts.debater_system(who, topic), prompts.research_prompt(topic, ctx, self.state.get("sources", [])),
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
        progress.set_phase("Openings")
        turns = self._both(lambda who: self.agents[who].ask(
            prompts.debater_system(who, topic), prompts.opening_prompt(topic, ctx, memos, self.state.get("sources", [])),
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
            progress.set_phase(f"Round {r}/{self.state['max_rounds']}")
            turns: dict = {}
            for who in (first, second):
                opp = prompts.OTHER[who]
                opp_turn = turns.get(opp) or prev["turns"].get(opp)
                nudge = ledger.get(f"nudge_{who}", "")
                turns[who] = self.agents[who].ask(
                    prompts.debater_system(who, topic),
                    prompts.turn_prompt(who, topic, ctx, memos, ledger, opp_turn, prev["turns"].get(who),
                                        nudge, self.state["facts"], r, self.state["max_rounds"],
                                        self.state.get("opinions", [])),
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
        progress.set_phase("Closings")
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
        progress.set_phase("Synthesis")
        s["synthesis"] = self.agents["referee"].ask(
            prompts.synthesis_system(s["topic"]),
            prompts.synthesis_prompt(s["topic"], s["context"], s["rounds"][-1]["ledger"], s["closings"], s["memos"],
                                     s["facts"], s.get("opinions", [])),
            schemas.SYNTHESIS, web=False, what="synthesis")
        self._advance("done")

    # ------------------------------------------------------------ referee & termination

    def _referee(self, ledger: dict | None, turns: dict, round_no: int, prev_ledger: dict | None) -> dict:
        if self.judge is not None:
            new = self._referee_judged(ledger, turns, round_no)
            counts = _status_counts(new)
            self._tx(f"\n### Referee after round {round_no}\n\n{new['round_summary']}\n\nStatus: {counts}\n\n"
                     + _judge_md(new, ledger) + "\n")
            log.info("ledger after round %d: %s", round_no, counts)
            progress.ledger(round_no, _status_tally(new))
            return new
        new = self.agents["referee"].ask(
            prompts.referee_system(self.state["topic"]),
            prompts.referee_prompt(self.state["topic"], ledger, turns, round_no, prev_ledger, self.state["facts"],
                                   self.state.get("opinions", [])),
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
        progress.ledger(round_no, _status_tally(new))
        return new

    def _referee_judged(self, ledger: dict | None, turns: dict, round_no: int) -> dict:
        """Jev judges every claim; the scribe writes the prose; code owns IDs, statuses and flags."""
        topic, facts, opinions = self.state["topic"], self.state["facts"], self.state.get("opinions", [])
        claims = [dict(c) for c in (ledger["claims"] if ledger else [])]
        # 1. New claims: dedup against existing ones with the judge, number them in code.
        new_by: dict[str, str] = {}
        for who in ("claude", "codex"):
            for nc in turns.get(who, {}).get("new_claims", []):
                existing = [(c["id"], c["claim"]) for c in claims]
                dup = judging.judge_duplicate(self.judge, topic, nc["claim"], existing)
                best = max(dup, key=dup.get) if dup else None
                if best and dup[best] >= judging.DUPLICATE_THRESHOLD:
                    target = next(c for c in claims if c["id"] == best)
                    if target.get("origin") != who:
                        target["origin"] = "both"
                    log.info("%s's new claim merged into %s (p=%.2f)", prompts.DISPLAY[who], best, dup[best])
                    continue
                cid = f"K{len(claims) + 1}"
                claims.append({"id": cid, "claim": nc["claim"], "origin": who, "status": "open",
                               "claude_position": nc["reasoning"] if who == "claude" else "",
                               "codex_position": nc["reasoning"] if who == "codex" else "",
                               "crux": "", "sources": list(nc.get("sources", []))})
                new_by[cid] = who
        # 2. Judge every claim on this round's material only.
        states = {}
        for c in claims:
            responses = {who: next((r for r in turns.get(who, {}).get("responses", []) if r["claim_id"] == c["id"]), None)
                         for who in ("claude", "codex")}
            requests = {who: next((q for q in turns.get(who, {}).get("evidence_requests", []) if q["claim_id"] == c["id"]), None)
                        for who in ("claude", "codex")}
            states[c["id"]] = judging.claim_state(topic, c, round_no, responses, requests, new_by.get(c["id"]), facts, opinions)
            for who, r in responses.items():
                if r:
                    c["sources"] = (c.get("sources") or []) + list(r.get("sources", []))
        verdicts = judging.judge_all(self.judge, states)
        flags = {"claude": [], "codex": []}
        needs_human_ids = []
        for c in claims:
            j = verdicts[c["id"]]
            prev_status = c["status"] if ledger else None
            c["status"] = j["status"]
            c["judge"] = {**j, "previous_status": prev_status}
            if c["status"] in ("disputed", "open"):
                for who in ("claude", "codex"):
                    if j["repeats"][who] >= 0.5 and round_no > 0:
                        flags[who].append(c["id"])
                if j["human_needed"] >= judging.HUMAN_THRESHOLD or (j["crux_kind"] == "value_judgement" and c["status"] == "disputed"):
                    needs_human_ids.append(c["id"])
        # 3. The scribe writes the words; fixed fields are re-applied afterwards.
        prose = self.agents["referee"].ask(
            prompts.scribe_system(topic),
            prompts.scribe_prompt(topic, claims, turns, round_no, flags, needs_human_ids, facts, opinions),
            schemas.SCRIBE, web=False, what=f"scribe round {round_no}")
        by_id = {p["id"]: p for p in prose["claims"]}
        for c in claims:
            p = by_id.get(c["id"])
            if p:
                c["claude_position"], c["codex_position"] = p["claude_position"], p["codex_position"]
                c["crux"] = p["crux"] if c["status"] == "disputed" else ""
        return {
            "claims": claims, "round_summary": prose["round_summary"],
            "repetition_flags": [{"claim_id": cid, "who": who, "note": "maintained without new argument or evidence (judge)"}
                                 for who, ids in flags.items() for cid in ids],
            "nudge_claude": prose["nudge_claude"] if flags["claude"] else "",
            "nudge_codex": prose["nudge_codex"] if flags["codex"] else "",
            "needs_human": bool(needs_human_ids), "human_question": prose["human_question"] if needs_human_ids else "",
            "settled": not any(c["status"] in ("disputed", "open") for c in claims),
            "judged_by": self.judge.label,
        }

    def _should_stop(self, ledger: dict, turns: dict) -> bool:
        rounds = self.state["rounds"]
        r = rounds[-1]["round"]
        if ledger["settled"]:
            return self._stop("All claims settled.")
        if all(t["nothing_new"] for t in turns.values()):
            return self._stop("Both sides declared they had nothing new to add.")
        stable = 1
        for a, b in zip(reversed(rounds), list(reversed(rounds))[1:]):
            if _statuses(a["ledger"]) == _statuses(b["ledger"]):
                stable += 1
            else:
                break
        stalled = stable > self.cfg.stable_rounds
        on = self.cfg.pause_on
        if stalled and "stall" not in on:
            return self._stop(f"Ledger unchanged for {stable} rounds.")
        if ledger["needs_human"] and "referee" not in on:
            log.info("referee asked for a decision; pause_on has no 'referee', continuing: %s",
                     ledger["human_question"][:200])
        reasons = self._pause_reasons(ledger, r, stable, stalled)
        if reasons:
            q = f"Round {r}. " + "\n".join(reasons) + "\n\nRemaining disputes:\n" + _disputes_md(ledger)
            reply = self.checkpoint(q, ["continue", "stop", "opinion: <text>", "fact: <text>"])
            if not self._handle_reply(reply, r):
                return True
        return False

    def _pause_reasons(self, ledger: dict, round_no: int, stable: int, stalled: bool) -> list[str]:
        """Which of the configured pause_on situations hold after this round."""
        counts = _status_tally(ledger)
        names = {**counts, "round": round_no, "unchanged": stable - 1, "total": len(ledger["claims"])}
        out = []
        for t in self.cfg.pause_on:
            if t == "referee" and ledger["needs_human"]:
                out.append(f"The referee needs a decision:\n\n{ledger['human_question']}")
            elif t == "stall" and stalled:
                out.append(f"No claim has changed status for {stable} rounds.")
            elif t == "every_round":
                out.append("You asked to be consulted after every round.")
            elif t == "disputes" and counts["disputed"]:
                out.append(f"{counts['disputed']} claim(s) still disputed.")
            elif t == "agree_to_disagree" and counts["agree_to_disagree"]:
                out.append(f"{counts['agree_to_disagree']} claim(s) marked agree-to-disagree.")
            elif t == "low_confidence":
                shaky = [f"{c['id']} ({c['judge']['status_confidence']:.2f})" for c in ledger["claims"]
                         if c.get("judge") and c["judge"]["status_confidence"] < judging.LOW_CONFIDENCE]
                if shaky:
                    out.append("The judge was unsure about: " + ", ".join(shaky) + ".")
            elif t.startswith("round:") and round_no == int(t[6:]):
                out.append(f"You asked to be consulted after round {round_no}.")
            elif t.startswith("custom:"):
                expr = t[7:]
                try:
                    if eval(expr, {"__builtins__": {}}, names):
                        out.append(f"Your condition `{expr}` is true ({names}).")
                except Exception as e:  # a bad expression must not kill a long run
                    log.warning("pause_on custom %r failed: %s", expr, e)
        return out

    def _finish_or_extend(self, ledger: dict) -> bool:
        """At the round cap. Returns True to keep going (cap raised), False to finish."""
        if ledger["settled"] or self.cfg.unattended:
            self._stop(f"Reached the round cap ({self.state['max_rounds']}).")
            return False
        reply = self.checkpoint(
            f"Round cap of {self.state['max_rounds']} reached with unresolved claims:\n" + _disputes_md(ledger),
            ["stop", "extend <n>", "opinion: <text>", "fact: <text>"])
        m = re.search(r"extend\s+(\d+)", reply)
        if m:
            self.state["max_rounds"] += int(m.group(1))
            rest = re.sub(r"extend\s+\d+", "", reply).strip(" ,.;")
            if rest:
                self._record_input(rest, self.state["max_rounds"])
            self._save()
            return True
        if reply.lower() not in ("stop", "continue"):
            self._record_input(reply, self.state["max_rounds"])
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
        if low == "continue":
            return True
        self._record_input(reply, round_no)
        return True

    def _record_input(self, reply: str, round_no: int):
        """`opinion: ...` is a non-binding view; `fact: ...` (or anything else) is binding."""
        m = re.match(r"(?i)\s*(?:opinion|o)\s*:\s*(.+)", reply, re.S)
        if m:
            self._add_opinion(m.group(1).strip(), round_no)
        else:
            self._add_fact(re.sub(r"(?i)^\s*(?:fact|f)\s*:\s*", "", reply).strip(), round_no)

    def _add_opinion(self, text: str, round_no: int):
        self.state["opinions"].append(f"(after round {round_no}) {text}")
        self._tx(f"\n> **Human opinion after round {round_no} (not binding):** {text}\n")
        self._save()

    def _add_fact(self, text: str, round_no: int):
        self.state["facts"].append(f"(after round {round_no}) {text}")
        self._tx(f"\n> **Fact set by the human after round {round_no} (binding):** {text}\n")
        self._save()

    def _stop(self, reason: str) -> bool:
        self.state["stop_reason"] = reason
        self._tx(f"\n> **Debate ended:** {reason}\n")
        log.info("stop: %s", reason)
        progress.set_phase("Wrapping up")
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
        out = self.files.report
        out.write_text(render_report(self.state, self.agents))
        log.info("report written: %s", out)
        log.info("review written: %s", write_review(self.files, self.state))
        return out


def _statuses(ledger: dict) -> dict:
    return {c["id"]: c["status"] for c in ledger["claims"]}


def _judge_md(new: dict, old: dict | None) -> str:
    """One line per claim with the judge's verdict, for the transcript."""
    lines = []
    for c in new["claims"]:
        j = c.get("judge")
        if not j:
            continue
        prev = j.get("previous_status")
        arrow = f"{prev}→{c['status']}" if prev and prev != c["status"] else c["status"]
        lines.append(f"- {c['id']}: {arrow} ({j['status_confidence']:.2f}), moved {j['moved']}, "
                     f"lean {j['lean']} ({j['lean_confidence']:.2f})")
    return "Judge verdicts:\n" + "\n".join(lines) if lines else ""


def _status_tally(ledger: dict) -> dict:
    t = {k: 0 for k in ("open", "disputed", "agreed", "conceded", "agree_to_disagree")}
    for c in ledger["claims"]:
        t[c["status"]] = t.get(c["status"], 0) + 1
    return t


def _status_counts(ledger: dict) -> str:
    counts: dict[str, int] = {}
    for c in ledger["claims"]:
        counts[c["status"]] = counts.get(c["status"], 0) + 1
    return ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) or "no claims"


def _disputes_md(ledger: dict) -> str:
    rows = [c for c in ledger["claims"] if c["status"] in ("disputed", "open")]
    return "\n".join(f"- {c['id']}: {c['claim']}\n    crux: {c['crux']}" for c in rows) or "(none)"
