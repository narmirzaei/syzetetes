"""The judge: typed, calibrated rulings on every claim after every round, made by Jev (TypeSafe AI).

Jev is a decision model: it takes a state plus typed questions and returns a choice / score / yes-no with
probabilities. It writes no text. The LLM referee writes the ledger; the judge then rules independently on
each claim (status, who moved, repetition, crux kind, which case is stronger, whether a human is needed).
Agreement attaches a confidence to the referee's status; disagreement marks the claim contested and, when
the judge is confident, is put to the debaters and the referee in the next round.

Jev's documented weaknesses, and how each is handled here:
  - context rot on large state   -> one small state per claim: only this round's material about it
  - first-option bias in choices -> every choice is asked twice with the options reversed; probabilities averaged
  - multi-hop questions          -> each question is one judgment; combinations are done in code
  - counting / arithmetic        -> never asked; `settled`, stalls and thresholds are computed in code

API: POST https://api.typesafe.ai/v1/systemone with a bearer key from $TYPESAFE_API_KEY or
~/.config/syzetetes/credentials.toml (see config.api_key). Zero dependencies.
"""
from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from pathlib import Path
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor

from . import config as conf
from .ui import progress

log = logging.getLogger("syzetetes")

ENDPOINT = "https://api.typesafe.ai/v1/systemone"
ENV_KEY = "TYPESAFE_API_KEY"
DEFAULT_MODEL = "jev-latest"
MAX_FIELD_CHARS = 6000          # per text field in a claim state; keeps each question far below 32k tokens
HUMAN_THRESHOLD = 0.7
FEEDBACK_THRESHOLD = 0.7        # a contested ruling at or above this goes to the debaters next round
LOW_CONFIDENCE = 0.6

STATUSES = {
    "agreed": "both sides now hold the claim",
    "conceded": "one side explicitly accepted the other side's claim",
    "disputed": "the positions differ and at least one side still has arguments or evidence to offer",
    "agree_to_disagree": "both sides said they agree to disagree, or the disagreement is a value judgement "
                         "or rests on evidence that does not exist",
    "open": "the claim was raised but the other side has not yet answered it",
}
MOVED = {"claude": "Claude changed position on this claim this round",
         "codex": "Codex changed position on this claim this round",
         "both": "both sides changed position this round",
         "neither": "neither side changed position this round"}
CRUX_KIND = {"factual": "a question of fact that evidence could settle",
             "value_judgement": "a value judgement that evidence cannot settle",
             "scope_or_definition": "a question of scope or definition that changes the answer",
             "missing_evidence": "evidence that would settle it does not exist or cannot be found",
             "none": "there is no real disagreement left"}
LEAN = {"claude": "Claude's case on this claim is currently stronger",
        "codex": "Codex's case on this claim is currently stronger",
        "even": "the two cases are about equally strong, or the claim is not in dispute"}


class JudgeError(RuntimeError):
    pass



class Judge(ABC):
    """Anything that answers typed questions about a state. Jev is the real one; tests use a fake."""
    label = "judge"

    @abstractmethod
    def ask(self, state: dict, questions: dict) -> dict:
        """Returns Jev's `answers` object: name -> {type, choice|noul|score, probabilities?, confidence?}."""


class JevJudge(Judge):
    def __init__(self, model: str = DEFAULT_MODEL, api_key: str | None = None, timeout_s: int = 60, retries: int = 4):
        self.model = model
        self.api_key = api_key or conf.api_key(ENV_KEY)
        self.timeout_s, self.retries = timeout_s, retries
        self.label = f"Jev ({model})"
        self.calls = 0
        self.input_tokens = 0
        if not self.api_key:
            raise JudgeError(f"no {ENV_KEY}: export it, or run `syzetetes key` to store it in {conf.CREDENTIALS} "
                             f"(get one at https://console.typesafe.ai/keys); running without the judge, so no confidences "
                             f"and no contested claims. --judge none silences this.")

    def ask(self, state: dict, questions: dict) -> dict:
        body = json.dumps({"model": self.model, "state": state, "questions": questions}, ensure_ascii=False).encode()
        req = urllib.request.Request(ENDPOINT, data=body, method="POST", headers={
            "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        delay = 1.0
        for attempt in range(1, self.retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_s) as r:
                    data = json.loads(r.read())
                self.calls += 1
                self.input_tokens += int(data.get("usage", {}).get("input_tokens", 0))
                return data["answers"]
            except urllib.error.HTTPError as e:
                detail = e.read().decode(errors="replace")[:500]
                if e.code in (429, 529) and attempt < self.retries:
                    log.warning("Jev %s; retrying in %.0fs", e.code, delay)
                    time.sleep(delay)
                    delay *= 2
                    continue
                if e.code == 401:
                    raise JudgeError(f"Jev rejected the API key in ${ENV_KEY} (401)") from None
                raise JudgeError(f"Jev HTTP {e.code}: {detail}") from None
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as e:
                if attempt < self.retries:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise JudgeError(f"Jev unreachable: {e}") from None
        raise JudgeError("Jev: retries exhausted")


# ---------------------------------------------------------------- question helpers

def _choice(instructions: str, criteria: dict, reverse: bool) -> dict:
    items = list(criteria.items())
    if reverse:
        items.reverse()
    return {"type": "choice", "instructions": instructions, "criteria": dict(items)}


def _noul(instructions: str, true: str = "", false: str = "") -> dict:
    q = {"type": "noul", "instructions": instructions}
    if true or false:
        q["criteria"] = {"true": true, "false": false}
    return q


def _merge_choice(a: dict, b: dict) -> tuple[str, float, dict]:
    """Average two orderings of the same choice question. Returns (choice, confidence, probabilities)."""
    keys = set(a.get("probabilities", {})) | set(b.get("probabilities", {}))
    probs = {k: (a.get("probabilities", {}).get(k, 0) + b.get("probabilities", {}).get(k, 0)) / 2 for k in keys}
    choice = max(probs, key=probs.get) if probs else a.get("choice", "")
    conf = (float(a.get("confidence", 0)) + float(b.get("confidence", 0))) / 2
    return choice, round(conf, 3), {k: round(v, 3) for k, v in probs.items()}


def _trim(text, n: int = MAX_FIELD_CHARS):
    if isinstance(text, str) and len(text) > n:
        return text[:n] + " […]"
    return text


# ---------------------------------------------------------------- per-claim judgment

def claim_state(topic: str, claim: dict, round_no: int, responses: dict, requests: dict,
                new_by: str | None, facts: list[str], opinions: list[str]) -> dict:
    """The small, focused state Jev sees for one claim. `responses` / `requests`: who -> this round's
    structured response / evidence request about this claim (or None)."""
    return {
        "topic": topic,
        "round": round_no,
        "claim": {"id": claim["id"], "text": _trim(claim["claim"]), "raised_by": claim.get("origin", new_by or ""),
                  "status_before_this_round": claim.get("status", "new this round"),
                  "claude_position_before": _trim(claim.get("claude_position", "")),
                  "codex_position_before": _trim(claim.get("codex_position", "")),
                  "crux_before": _trim(claim.get("crux", ""))},
        "this_round": {
            who: ({"stance": r["stance"], "reasoning": _trim(r["reasoning"]),
                   "revised_claim": _trim(r.get("revised_claim", "")),
                   "sources": [{"title": s.get("title", ""), "note": s.get("note", "")} for s in r.get("sources", [])][:8]}
                  if r else ("raised this claim this round" if new_by == who else "did not address this claim"))
            for who, r in responses.items()},
        "evidence_requests": {who: _trim(q["what_would_change_my_mind"]) for who, q in requests.items() if q},
        "human_facts_binding": facts,
        "human_opinions_not_binding": opinions,
    }


def claim_questions(reverse: bool) -> dict:
    return {
        "status": _choice("After this round, what is the status of this claim?", STATUSES, reverse),
        "moved": _choice("Who changed their position on this claim this round?", MOVED, reverse),
        "crux_kind": _choice("If the claim is still disputed, what kind of disagreement is it?", CRUX_KIND, reverse),
        "lean": _choice("Judging only the arguments and evidence given, whose case on this claim is stronger right now?",
                        LEAN, reverse),
        "repeats_claude": _noul("Claude maintained its position on this claim without any new argument or new evidence",
                                "Claude restated what it had said before", "Claude added a new argument, new evidence, or changed position"),
        "repeats_codex": _noul("Codex maintained its position on this claim without any new argument or new evidence",
                               "Codex restated what it had said before", "Codex added a new argument, new evidence, or changed position"),
        "answered_request": _noul("The evidence request about this claim was directly answered this round",
                                  "the requested evidence or a direct reply was given", "no request was made, or it was ignored or deflected"),
        "human_needed": _noul("The two sides cannot make further progress on this claim without a decision from the human "
                              "(conflicting sources no search can resolve, a pure value judgement, or a scope question)",
                              "a human decision is needed to move on", "the debaters can still progress on their own"),
    }


def judge_claim(judge: Judge, state: dict) -> dict:
    """Ask every per-claim question twice (options forward and reversed) and merge. Returns the `judge` block."""
    a = judge.ask(state, claim_questions(reverse=False))
    b = judge.ask(state, claim_questions(reverse=True))
    status, s_conf, s_probs = _merge_choice(a["status"], b["status"])
    moved, _, _ = _merge_choice(a["moved"], b["moved"])
    crux_kind, _, _ = _merge_choice(a["crux_kind"], b["crux_kind"])
    lean, l_conf, l_probs = _merge_choice(a["lean"], b["lean"])
    noul = lambda k: round((float(a[k]["noul"]) + float(b[k]["noul"])) / 2, 3)
    return {
        "status": status, "status_confidence": s_conf, "status_probabilities": s_probs,
        "moved": moved, "crux_kind": crux_kind,
        "lean": lean, "lean_confidence": l_conf, "lean_probabilities": l_probs,
        "repeats": {"claude": noul("repeats_claude"), "codex": noul("repeats_codex")},
        "answered_request": noul("answered_request"),
        "human_needed": noul("human_needed"),
    }


def judge_all(judge: Judge, states: dict[str, dict], workers: int = 4) -> dict[str, dict]:
    """Judge many claims in parallel; shows progress in the status line."""
    out = {}
    progress.task_start(judge.label, f"judging {len(states)} claims")
    try:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {cid: ex.submit(judge_claim, judge, st) for cid, st in states.items()}
            for cid, f in futs.items():
                out[cid] = f.result()
    finally:
        progress.task_end(judge.label)
    return out


def make_judge(kind: str, model: str) -> Judge:
    if kind != "jev":
        raise JudgeError(f"unknown judge {kind!r}")
    return JevJudge(model)
