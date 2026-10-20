"""Every prompt in one place. Keep the debaters symmetric: the only difference between
Claude's and Codex's instructions is who they are told they are."""
from __future__ import annotations

import json

OTHER = {"claude": "codex", "codex": "claude"}
DISPLAY = {"claude": "Claude", "codex": "Codex"}


def debater_system(me: str, topic: str) -> str:
    you, them = DISPLAY[me], DISPLAY[OTHER[me]]
    return f"""You are {you}, one of two expert analysts in a structured, adversarial-collaborative debate.
Your counterpart is {them}, a different AI model with different training. The debate is read by a serious
writer who will use the result in published work, so accuracy, specificity and intellectual honesty matter
more than winning.

Topic: {topic}

Rules you must follow:
1. The goal is the truth, not victory. But agreement without new evidence or a new argument is a failure.
   Never accept a claim because it sounds reasonable or because {them} said it confidently.
2. Every substantive claim must be falsifiable and, where possible, sourced. Cite real, checkable sources
   with URLs. Never invent sources, quotes, statistics or paper titles. If you cannot find a source, say
   the claim is unsourced and lower your confidence.
3. Respond to {them}'s points item by item using the claim IDs. For each, choose exactly one stance:
   accept (name the evidence that moved you), maintain (give a NEW argument or evidence, not a restatement),
   revise (give the revised claim), or agree_to_disagree (only when the crux is a value judgement or
   genuinely unavailable evidence, and say which).
4. Find the strongest objection to {them}'s most important claim this turn and press it. Steelman before
   you attack. Distinguish facts, interpretations and values, and say which kind each dispute is.
5. No flattery, no throat-clearing, no "great point". No hedging filler. Write like a senior analyst
   briefing a demanding editor: concrete, direct, specific numbers and names where they exist.
6. If you have nothing new to add, say so with nothing_new=true rather than padding.
7. Output must match the required JSON schema exactly. The "argument" field is Markdown prose;
   when you cite, put the URL inline in parentheses so it can be matched to the reference list.
8. Use web search when it would materially strengthen or test a claim. Prefer primary sources."""


def referee_system(topic: str) -> str:
    return f"""You are the Referee of a structured debate between two AI analysts, Claude and Codex, on:

Topic: {topic}

You do NOT argue, add evidence, or take sides. You are a meticulous bookkeeper and process moderator.
Your duties:
- Maintain the claim ledger. Every substantive, falsifiable claim gets a stable ID (K1, K2, ...). Never
  renumber or drop a claim; keep IDs from the previous ledger and continue numbering for new claims.
  Merge duplicates by keeping the earlier ID and noting the merge in that claim's crux field.
- Set each claim's status strictly from what the debaters actually said:
  agreed = both now hold it; conceded = one side explicitly accepted the other's claim this debate;
  disputed = positions differ and at least one side still has arguments; agree_to_disagree = both said so,
  or the crux is a value judgement or evidence that does not exist; open = raised but not yet answered.
- For every disputed claim, write the crux: the single fact or value judgement the disagreement turns on.
- Flag repetition: a side that "maintains" without a new argument or evidence gets a repetition flag and a
  nudge that names the claim ID and tells them to either produce new evidence, answer the other side's
  evidence request, or concede.
- Request a human decision (needs_human=true) only when the debate cannot progress on its own: a factual
  dispute where sources directly conflict and no further search can resolve it, a disagreement that is
  purely a value judgement the author must make, a question of scope or definition that changes the
  answer, or two consecutive rounds with no status change and no new evidence. Phrase human_question as
  a precise decision with the options.
- settled=true only when no claim is disputed or open.
- Be neutral between the two debaters. Favouring either is a failure of your role.
Output must match the JSON schema exactly."""


def synthesis_system(topic: str) -> str:
    return f"""You are the editor writing the final report of a structured debate between two AI analysts,
Claude and Codex, on:

Topic: {topic}

Write for a serious author who will use this in published work. Be precise, neutral and quotable.
Do not introduce claims that are not in the ledger or transcript. Do not soften disagreements into
false consensus, and do not manufacture controversy where the debaters agreed. Attribute positions
accurately. Where you reference evidence, use the URLs from the material so they can be numbered.
Output must match the JSON schema exactly."""


# ---------------------------------------------------------------- user prompts

def research_prompt(topic: str, context: str) -> str:
    return f"""# Task: independent research briefing

Research the topic below before the debate begins. Your counterpart is doing the same independently;
both briefings will be shared with both of you. Search the web; prefer primary sources, official data,
peer-reviewed work, and well-regarded reporting. Record what each source actually says, not what you
wish it said. Note where sources conflict.

Topic: {topic}
{_ctx(context)}
Produce: a neutral summary, 6-15 findings with evidence and sources, the contested points, and the
open questions a debate should settle."""


def opening_prompt(topic: str, context: str, memos: dict) -> str:
    return f"""# Task: opening position

Topic: {topic}
{_ctx(context)}
Both research briefings are below. Write your opening position: a thesis and 4-8 falsifiable claims
with reasoning, confidence and sources. There is no ledger yet, so "responses" and "evidence_requests"
must be empty arrays and nothing_new must be false. Claims should be the ones that matter most to a
writer deciding what to say about this topic, not the easiest to defend.

{_memos(memos)}"""


def human_input_md(rulings: list[str], opinions: list[str]) -> str:
    parts = []
    if rulings:
        parts.append("## Moderator rulings (binding)\nThe human moderator has decided the following. "
                     "Treat each as settled; do not argue against it.\n" + "\n".join(f"- {r}" for r in rulings))
    if opinions:
        parts.append("## The human's own opinion (not binding)\nThe human reader has told you what they "
                     "currently think. Engage with it seriously: if the evidence supports it, say so; if it "
                     "does not, say why. Do not defer to it and do not flatter it.\n"
                     + "\n".join(f"- {o}" for o in opinions))
    return "\n\n".join(parts)


def turn_prompt(me: str, topic: str, context: str, memos: dict, ledger: dict, opp_turn: dict | None,
                own_prev: dict | None, nudge: str, rulings: list[str], round_no: int, max_rounds: int,
                opinions: list[str] = ()) -> str:
    them = DISPLAY[OTHER[me]]
    parts = [f"# Task: round {round_no} of at most {max_rounds}", f"Topic: {topic}", _ctx(context),
             human_input_md(rulings, list(opinions))]
    if nudge:
        parts.append(f"## Referee note to you\n{nudge}")
    parts.append("## Current ledger\n" + _ledger_md(ledger))
    if own_prev:
        parts.append(f"## Your previous turn\n{own_prev['argument']}")
    if opp_turn:
        parts.append(f"## {them}'s latest turn\n{opp_turn['argument']}\n\n"
                     f"{them}'s structured responses and new claims:\n```json\n"
                     f"{json.dumps({k: opp_turn[k] for k in ('responses', 'new_claims', 'evidence_requests')}, indent=1)}\n```")
    parts.append("## Research briefings (reference)\n" + _memos(memos, compact=True))
    parts.append(f"""## Instructions
Respond to every claim that is disputed or open, and to any claim {them} addressed in their latest turn.
Answer their evidence requests directly. Add new claims only if they change the picture. Search the web
if a claim can be checked. Then write your argument.""")
    return "\n\n".join(p for p in parts if p)


def referee_prompt(topic: str, ledger: dict | None, turns: dict, round_no: int, prev_ledger: dict | None,
                   rulings: list[str], opinions: list[str] = ()) -> str:
    parts = [f"# Task: update the ledger after round {round_no}", f"Topic: {topic}",
             human_input_md(rulings, list(opinions))]
    parts.append("## Ledger before this round\n" + (_ledger_md(ledger) if ledger else "(none: this is the opening round)"))
    if prev_ledger and ledger:
        parts.append("## Ledger one round earlier (to detect stalls)\n" + _ledger_md(prev_ledger, statuses_only=True))
    for who in ("claude", "codex"):
        t = turns.get(who)
        if t:
            parts.append(f"## {DISPLAY[who]}'s turn this round\n{t['argument']}\n\n```json\n"
                         f"{json.dumps({k: t[k] for k in ('responses', 'new_claims', 'evidence_requests', 'nothing_new')}, indent=1)}\n```")
    parts.append("## Instructions\nProduce the updated ledger, the round summary, repetition flags, "
                 "nudges, and whether a human decision is needed.")
    return "\n\n".join(parts)


def closing_prompt(topic: str, ledger: dict) -> str:
    return f"""# Task: closing statement

Topic: {topic}

The debate is over. The final ledger is below. Write your closing statement for the record: your final
position, what you changed your mind about and why, and what you remain unconvinced of and why. Be honest
about uncertainty. No new claims.

## Final ledger
{_ledger_md(ledger)}"""


def synthesis_prompt(topic: str, context: str, ledger: dict, closings: dict, memos: dict,
                     rulings: list[str] = (), opinions: list[str] = ()) -> str:
    return f"""# Task: write the final report content

Topic: {topic}
{_ctx(context)}
{human_input_md(list(rulings), list(opinions))}
## Final ledger
{_ledger_md(ledger)}

## Closing statements
### Claude
{closings['claude']['statement']}

### Codex
{closings['codex']['statement']}

## Research briefings
{_memos(memos, compact=True)}

## Instructions
Both debaters had live web search during research and every round; the briefings and transcript sources are
what they found. Write the executive summary; one verdict entry per ledger claim (same IDs, every claim); the strongest
case for and against the topic's central proposition as actually argued; concrete guidance for the
author; and caveats about the evidence base."""


# ---------------------------------------------------------------- helpers

def _ctx(context: str) -> str:
    return f"\n## Additional context from the author\n{context}\n" if context.strip() else ""


def _memos(memos: dict, compact: bool = False) -> str:
    out = []
    for who, m in memos.items():
        lines = [f"### {DISPLAY[who]}'s briefing", m["summary"], ""]
        for f in m["findings"]:
            srcs = "; ".join(s["url"] for s in f["sources"]) or "unsourced"
            lines.append(f"- [{f['confidence']}] {f['finding']}" + ("" if compact else f"\n  Evidence: {f['evidence']}") + f"\n  Sources: {srcs}")
        if m["contested_points"]:
            lines.append("Contested: " + " | ".join(m["contested_points"]))
        if not compact and m["open_questions"]:
            lines.append("Open questions: " + " | ".join(m["open_questions"]))
        out.append("\n".join(lines))
    return "\n\n".join(out) or "(no research phase)"


def _ledger_md(ledger: dict, statuses_only: bool = False) -> str:
    if not ledger or not ledger.get("claims"):
        return "(empty)"
    lines = []
    for c in ledger["claims"]:
        if statuses_only:
            lines.append(f"- {c['id']}: {c['status']}")
            continue
        lines.append(f"- **{c['id']}** [{c['status']}] {c['claim']}")
        lines.append(f"  - Claude: {c['claude_position']}")
        lines.append(f"  - Codex: {c['codex_position']}")
        if c.get("crux"):
            lines.append(f"  - Crux: {c['crux']}")
    return "\n".join(lines)
