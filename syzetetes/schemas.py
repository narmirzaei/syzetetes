"""JSON schemas for every structured exchange, plus a small dependency-free validator.

Both CLIs enforce the schema server-side, but we validate again locally because
a malformed answer must be caught and re-asked rather than silently rendered.
Every property is required and additionalProperties is false, which is what
OpenAI's strict structured output demands.
"""
from __future__ import annotations

from typing import Any

CONFIDENCE = {"type": "string", "enum": ["high", "medium", "low"]}
STR_LIST = {"type": "array", "items": {"type": "string"}}


def _obj(props: dict, **kw) -> dict:
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False, **kw}


SOURCE = _obj({
    "url": {"type": "string"},
    "title": {"type": "string"},
    "note": {"type": "string", "description": "What this source actually supports, in one sentence."},
})

RESEARCH = _obj({
    "summary": {"type": "string", "description": "Neutral 150-300 word briefing on the state of evidence."},
    "findings": {"type": "array", "items": _obj({
        "finding": {"type": "string"},
        "evidence": {"type": "string", "description": "The specific data, quote, or result, not a paraphrase of the claim."},
        "confidence": CONFIDENCE,
        "sources": {"type": "array", "items": SOURCE},
    })},
    "contested_points": STR_LIST,
    "open_questions": STR_LIST,
})

CLAIM = _obj({
    "claim": {"type": "string", "description": "One falsifiable sentence."},
    "reasoning": {"type": "string"},
    "confidence": CONFIDENCE,
    "sources": {"type": "array", "items": SOURCE},
})

TURN = _obj({
    "argument": {"type": "string", "description": "Markdown. The substantive argument for this turn, 300-900 words."},
    "responses": {"type": "array", "items": _obj({
        "claim_id": {"type": "string"},
        "stance": {"type": "string", "enum": ["accept", "maintain", "revise", "agree_to_disagree"]},
        "reasoning": {"type": "string", "description": "Why. For 'accept', name the specific evidence that moved you."},
        "revised_claim": {"type": "string", "description": "Only for 'revise'; otherwise empty string."},
        "sources": {"type": "array", "items": SOURCE},
    })},
    "new_claims": {"type": "array", "items": CLAIM},
    "evidence_requests": {"type": "array", "items": _obj({
        "claim_id": {"type": "string"},
        "what_would_change_my_mind": {"type": "string"},
    })},
    "nothing_new": {"type": "boolean", "description": "True only if you have no new argument or evidence to add."},
})

LEDGER_CLAIM = _obj({
    "id": {"type": "string"},
    "claim": {"type": "string"},
    "origin": {"type": "string", "enum": ["claude", "codex", "both"]},
    "status": {"type": "string", "enum": ["agreed", "disputed", "conceded", "agree_to_disagree", "open"]},
    "claude_position": {"type": "string"},
    "codex_position": {"type": "string"},
    "crux": {"type": "string", "description": "For disputed claims: the single fact or value judgement the disagreement turns on."},
    "sources": {"type": "array", "items": SOURCE},
})

LEDGER = _obj({
    "claims": {"type": "array", "items": LEDGER_CLAIM},
    "round_summary": {"type": "string", "description": "2-4 neutral sentences on what moved this round."},
    "repetition_flags": {"type": "array", "items": _obj({
        "claim_id": {"type": "string"},
        "who": {"type": "string", "enum": ["claude", "codex", "both"]},
        "note": {"type": "string"},
    })},
    "nudge_claude": {"type": "string", "description": "Procedural instruction for Claude's next turn, or empty."},
    "nudge_codex": {"type": "string"},
    "needs_human": {"type": "boolean"},
    "human_question": {"type": "string", "description": "If needs_human: the precise decision the human must make and why the debaters cannot."},
    "settled": {"type": "boolean", "description": "True when no claim is 'disputed' or 'open'."},
})

# What the scribe writes when a decision model (Jev) has already judged every claim. Statuses, flags and
# crux kinds are fixed by code; the scribe only supplies words.
SCRIBE = _obj({
    "claims": {"type": "array", "items": _obj({
        "id": {"type": "string"},
        "claude_position": {"type": "string", "description": "Claude's current position on this claim, one or two sentences."},
        "codex_position": {"type": "string"},
        "crux": {"type": "string", "description": "For disputed claims: the single fact or value judgement it turns on. Else empty."},
    })},
    "round_summary": {"type": "string", "description": "2-4 neutral sentences on what moved this round, consistent with the fixed statuses."},
    "nudge_claude": {"type": "string", "description": "Procedural instruction for Claude's next turn, naming the flagged claim IDs, or empty."},
    "nudge_codex": {"type": "string"},
    "human_question": {"type": "string", "description": "If a human decision was requested: the precise decision with its options. Else empty."},
})

SYNTHESIS = _obj({
    "executive_summary": {"type": "string", "description": "Markdown, 200-400 words, for a reader who will not read the transcript."},
    "verdicts": {"type": "array", "items": _obj({
        "claim_id": {"type": "string"},
        "headline": {"type": "string", "description": "The claim restated as a clean, quotable sentence."},
        "explanation": {"type": "string", "description": "Why it ended where it did. Name the decisive evidence or the crux."},
    })},
    "strongest_case_for": {"type": "string"},
    "strongest_case_against": {"type": "string"},
    "what_the_author_should_do": {"type": "string", "description": "Concrete guidance for someone writing on this topic."},
    "caveats": STR_LIST,
})

CLOSING = _obj({
    "statement": {"type": "string", "description": "Markdown, 200-500 words. Your final position and what you changed your mind about."},
    "changed_my_mind_on": STR_LIST,
    "still_unconvinced_on": STR_LIST,
})


class SchemaError(ValueError):
    pass


def validate(obj: Any, schema: dict, path: str = "$") -> list[str]:
    """Return a list of human-readable problems; empty list means valid."""
    errs: list[str] = []
    t = schema.get("type")
    if "enum" in schema and obj not in schema["enum"]:
        return [f"{path}: {obj!r} not in {schema['enum']}"]
    if t == "object":
        if not isinstance(obj, dict):
            return [f"{path}: expected object"]
        for k in schema.get("required", []):
            if k not in obj:
                errs.append(f"{path}.{k}: missing")
        props = schema.get("properties", {})
        for k, v in obj.items():
            if k in props:
                errs += validate(v, props[k], f"{path}.{k}")
            elif schema.get("additionalProperties") is False:
                errs.append(f"{path}.{k}: unexpected key")
    elif t == "array":
        if not isinstance(obj, list):
            return [f"{path}: expected array"]
        for i, item in enumerate(obj):
            errs += validate(item, schema["items"], f"{path}[{i}]")
    elif t == "string":
        if not isinstance(obj, str):
            errs.append(f"{path}: expected string")
    elif t == "boolean":
        if not isinstance(obj, bool):
            errs.append(f"{path}: expected boolean")
    elif t in ("integer", "number"):
        if isinstance(obj, bool) or not isinstance(obj, (int, float)):
            errs.append(f"{path}: expected number")
    return errs
