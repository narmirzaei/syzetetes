"""Render the final Markdown report from the saved state.

The verdict sections are built from the ledger (the source of truth), with the
synthesis providing prose. Every URL that appeared anywhere becomes a numbered
reference, and inline URLs in prose are replaced by [n] markers.
"""
from __future__ import annotations

import re
from datetime import datetime

DISPLAY = {"claude": "Claude", "codex": "Codex"}
STATUS_TITLE = {
    "agreed": "Points of agreement",
    "conceded": "Points conceded during the debate",
    "disputed": "Points of disagreement",
    "agree_to_disagree": "Agreed to disagree",
    "open": "Open points",
}


class References:
    def __init__(self):
        self.order: list[str] = []
        self.meta: dict[str, dict] = {}

    @staticmethod
    def norm(url: str) -> str:
        return url.strip().rstrip(");.,;:'\"").rstrip("/")

    def add(self, src: dict):
        url = self.norm(src.get("url", ""))
        if not url.startswith("http"):
            return
        if url not in self.meta:
            self.order.append(url)
            self.meta[url] = {"title": "", "note": ""}
        m = self.meta[url]
        if not m["title"] and src.get("title"):
            m["title"] = src["title"].strip()
        if not m["note"] and src.get("note"):
            m["note"] = src["note"].strip()

    def num(self, url: str) -> int:
        return self.order.index(self.norm(url)) + 1

    def harvest(self, state: dict):
        def walk(o):
            if isinstance(o, dict):
                if "url" in o and isinstance(o.get("url"), str):
                    self.add(o)
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(state.get("memos"))
        walk(state.get("rounds"))
        walk(state.get("closings"))
        # Bare URLs that appear only in prose still deserve a reference entry.
        for text in _all_prose(state):
            for url in re.findall(r"https?://[^\s)\]>\"';,]+", text):
                self.add({"url": url})

    def cite(self, text: str) -> str:
        """Replace inline URLs with [n] markers, longest URLs first so prefixes do not clobber."""
        for url in sorted(self.order, key=len, reverse=True):
            n = self.num(url)
            esc = re.escape(url) + r"/?"
            text = re.sub(r"\[([^\]]+)\]\(" + esc + r"\)", rf"\1 [{n}]", text)      # [text](url)
            text = re.sub(r"\(\s*" + esc + r"\s*\)", f" [{n}]", text)               # (url)
            text = re.sub(r"(?<!\]\()" + esc + r"(?![\w/])", f"[{n}]", text)        # bare url, incl. inside (url; ...)
        return re.sub(r"[ \t]+\[(\d+)\]", r" [\1]", text)

    def section(self) -> str:
        if not self.order:
            return "_No sources were cited._"
        rows = []
        for i, url in enumerate(self.order, 1):
            m = self.meta[url]
            title = m["title"] or url
            line = f"{i}. {title}. <{url}>"
            if m["note"]:
                line += f" — {m['note']}"
            rows.append(line)
        return "\n".join(rows)


def _all_prose(state: dict):
    for m in state.get("memos", {}).values():
        yield m["summary"]
        for f in m["findings"]:
            yield f["evidence"]
    for r in state.get("rounds", []):
        for t in r["turns"].values():
            yield t["argument"]
    for c in state.get("closings", {}).values():
        yield c["statement"]
    if state.get("synthesis"):
        s = state["synthesis"]
        yield s["executive_summary"]
        yield s["strongest_case_for"]
        yield s["strongest_case_against"]


def render_report(state: dict, agents: dict | None = None) -> str:
    refs = References()
    refs.harvest(state)
    c = refs.cite
    topic = state["topic"]
    ledger = state["rounds"][-1]["ledger"] if state["rounds"] else {"claims": []}
    syn = state.get("synthesis") or {}
    verdicts = {v["claim_id"]: v for v in syn.get("verdicts", [])}
    cfg = state["config"]
    n_rounds = max((r["round"] for r in state["rounds"]), default=0)

    out: list[str] = []
    code = state.get("code")
    out.append(f"# {code + ' — ' if code else ''}{topic}\n")
    out.append("_A structured debate between two AI models, with independent research, "
               "a bookkeeping referee, and a numbered reference list._\n")
    out.append("| | |\n|---|---|")
    out.append(f"| Date | {state['created'][:10]} |")
    out.append(f"| Claude | {cfg['claude_model']} (effort: {cfg['claude_effort']}) |")
    out.append(f"| Codex | {cfg['codex_model']} (effort: {cfg['codex_effort']}) |")
    out.append(f"| Referee | {cfg['referee']} {cfg['referee_model']} (effort: {cfg['referee_effort']}) |")
    judged_by = (state["rounds"][-1]["ledger"].get("judged_by") if state.get("rounds") else None)
    if judged_by:
        n_con = sum(1 for k in ledger["claims"] if k.get("judge", {}).get("contested"))
        out.append(f"| Judge | {judged_by}: independent ruling on every claim; {n_con} final status(es) contested |")
    out.append(f"| Rounds | {n_rounds} after opening positions |")
    out.append(f"| Ended because | {state.get('stop_reason') or 'in progress'} |")
    out.append(f"| Claims | {_counts(ledger)} |")
    if state.get("context"):
        out.append(f"\n**Author's starting context.** {c(state['context'])}")
    if state.get("sources"):
        out.append("\n**Author's starting sources.**\n" + "\n".join(
            f"- S{i}: " + (c(x["ref"]) if x["kind"] == "url" else f"`{x['ref']}` (file)")
            for i, x in enumerate(state["sources"], 1)))
    if state.get("derived_from"):
        out.append(f"\n**Derived from** {state['derived_from']}.")
    if state.get("facts"):
        out.append("\n**Facts set by the human (binding).**\n" + "\n".join(f"- {r}" for r in state["facts"]))
    if state.get("opinions"):
        out.append("\n**Human's stated opinion (not binding).**\n" + "\n".join(f"- {o}" for o in state["opinions"]))

    if syn:
        out.append("\n## Executive summary\n\n" + c(syn["executive_summary"]))

    for status in ("agreed", "conceded", "disputed", "agree_to_disagree", "open"):
        rows = [k for k in ledger["claims"] if k["status"] == status]
        if not rows:
            continue
        out.append(f"\n## {STATUS_TITLE[status]}\n")
        for k in rows:
            v = verdicts.get(k["id"], {})
            out.append(f"### {k['id']}. {c(v.get('headline') or k['claim'])}\n")
            if status in ("disputed", "agree_to_disagree", "open"):
                out.append(f"- **Claude:** {c(k['claude_position'])}")
                out.append(f"- **Codex:** {c(k['codex_position'])}")
                if k.get("crux"):
                    out.append(f"- **Crux:** {c(k['crux'])}")
            elif status == "conceded":
                out.append(f"- **Claude:** {c(k['claude_position'])}")
                out.append(f"- **Codex:** {c(k['codex_position'])}")
            if v.get("explanation"):
                out.append(c(v["explanation"]))
            if k.get("judge"):
                j = k["judge"]
                lean = {"claude": "Claude's case stronger", "codex": "Codex's case stronger", "even": "cases even"}.get(j["lean"], j["lean"])
                if j.get("contested"):
                    out.append(f"\n*Judge disagrees: rules **{j['status'].replace('_', ' ')}** with confidence "
                               f"{j['status_confidence']:.2f} (referee: {status.replace('_', ' ')}); {lean} "
                               f"({j['lean_confidence']:.2f}); crux kind {j['crux_kind'].replace('_', ' ')}.*")
                else:
                    out.append(f"\n*Judge agrees: {status.replace('_', ' ')} with confidence {j['status_confidence']:.2f}; "
                               f"{lean} ({j['lean_confidence']:.2f}); crux kind {j['crux_kind'].replace('_', ' ')}.*")
            if k.get("sources"):
                out.append("\nSources: " + ", ".join(f"[{refs.num(s['url'])}]" for s in k["sources"]
                                                     if refs.norm(s["url"]) in refs.meta))
            out.append("")

    if syn:
        out.append("## Strongest case for\n\n" + c(syn["strongest_case_for"]))
        out.append("\n## Strongest case against\n\n" + c(syn["strongest_case_against"]))
        out.append("\n## Guidance for the author\n\n" + c(syn["what_the_author_should_do"]))
        if syn.get("caveats"):
            out.append("\n## Caveats\n\n" + "\n".join(f"- {c(x)}" for x in syn["caveats"]))

    if state.get("closings"):
        out.append("\n## Closing statements\n")
        for who in ("claude", "codex"):
            cl = state["closings"][who]
            out.append(f"### {DISPLAY[who]}\n\n{c(cl['statement'])}\n")
            if cl["changed_my_mind_on"]:
                out.append("Changed my mind on:\n" + "\n".join(f"- {c(x)}" for x in cl["changed_my_mind_on"]) + "\n")
            if cl["still_unconvinced_on"]:
                out.append("Still unconvinced on:\n" + "\n".join(f"- {c(x)}" for x in cl["still_unconvinced_on"]) + "\n")

    if state.get("memos"):
        out.append("## Research briefings\n")
        for who, m in state["memos"].items():
            out.append(f"### {DISPLAY[who]}\n\n{c(m['summary'])}\n")
            for f in m["findings"]:
                nums = ", ".join(f"[{refs.num(s['url'])}]" for s in f["sources"] if refs.norm(s["url"]) in refs.meta)
                out.append(f"- **{c(f['finding'])}** ({f['confidence']} confidence) {c(f['evidence'])} {nums}")
            if m["contested_points"]:
                out.append("\nContested points: " + "; ".join(c(x) for x in m["contested_points"]))
            out.append("")

    out.append("## Debate transcript\n")
    for r in state["rounds"]:
        title = "Opening positions" if r["round"] == 0 else f"Round {r['round']}"
        out.append(f"### {title}\n")
        order = ("claude", "codex") if r["first"] in ("both", "claude") else ("codex", "claude")
        for who in order:
            t = r["turns"].get(who)
            if not t:
                continue
            out.append(f"#### {DISPLAY[who]}\n\n{c(t['argument'])}\n")
            resp = [x for x in t["responses"] if x["stance"] != "maintain" or x["reasoning"]]
            if resp:
                out.append("Responses:\n" + "\n".join(
                    f"- {x['claim_id']} — **{x['stance']}**: {c(x['reasoning'])}"
                    + (f" Revised: {c(x['revised_claim'])}" if x["stance"] == "revise" and x["revised_claim"] else "")
                    for x in resp) + "\n")
            if t["evidence_requests"]:
                out.append("Evidence requests:\n" + "\n".join(
                    f"- {x['claim_id']}: {c(x['what_would_change_my_mind'])}" for x in t["evidence_requests"]) + "\n")
        lg = r["ledger"]
        out.append(f"**Referee.** {c(lg['round_summary'])} Status: {_counts(lg)}.\n")
        for fl in lg.get("repetition_flags", []):
            out.append(f"- Repetition flag on {fl['claim_id']} ({fl['who']}): {c(fl['note'])}")
        out.append("")

    out.append("## References\n\n" + refs.section())
    out.append(f"\n---\n_Generated {datetime.now():%Y-%m-%d %H:%M} by debate._\n")
    return "\n".join(out)


def _counts(ledger: dict) -> str:
    counts: dict[str, int] = {}
    for k in ledger["claims"]:
        counts[k["status"]] = counts.get(k["status"], 0) + 1
    return ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in sorted(counts.items())) or "none"
