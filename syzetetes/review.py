"""`syzetetes review D0001`: a self-contained interactive HTML page showing how the synthesis was reached.

The page embeds the run's state and renders, with no network access:
  - a claim-by-round grid: every claim's status at every round, colour-coded, clickable;
  - for a selected cell, both sides' positions, the crux, each debater's stance and reasoning on that
    claim that round, and the sources they cited;
  - the round strip: referee summaries, nudges, repetition flags, and where the human intervened;
  - the verdict column: the synthesis's per-claim headline and explanation;
  - closing statements and the executive summary.
"""
from __future__ import annotations

import json
from pathlib import Path

from .runs import RunFiles


def render_review(state: dict) -> str:
    # every "<" is escaped so neither "</script>" nor "<!--" can end or re-open the script element
    data = (json.dumps(_slim(state), ensure_ascii=False)
            .replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))
    return TEMPLATE.replace("__DATA__", data)


def write_review(files: RunFiles, state: dict) -> Path:
    out = files.review
    out.write_text(render_review(state))
    return out


def _slim(state: dict) -> dict:
    """Only what the page needs. Memos are large; keep summaries and findings without evidence blobs."""
    memos = {}
    for who, m in (state.get("memos") or {}).items():
        memos[who] = {"summary": m["summary"],
                      "findings": [{"finding": f["finding"], "confidence": f["confidence"],
                                    "sources": [s["url"] for s in f["sources"]]} for f in m["findings"]]}
    return {
        "code": state.get("code", ""), "topic": state["topic"], "context": state.get("context", ""),
        "config": state["config"], "created": state.get("created", ""), "stop_reason": state.get("stop_reason", ""),
        "derived_from": state.get("derived_from", ""), "sources": state.get("sources", []),
        "facts": state.get("facts", state.get("rulings", [])), "opinions": state.get("opinions", []),
        "memos": memos, "rounds": state["rounds"], "closings": state.get("closings", {}),
        "synthesis": state.get("synthesis"),
    }


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Syzetetes review</title>
<style>
:root{
  --bg:#f7f7f5;--panel:#ffffff;--ink:#1b1b1f;--muted:#6b6b72;--line:#e2e2df;--accent:#2f5bea;
  --agreed:#2f9e5b;--conceded:#7a5cc6;--disputed:#d8432b;--atd:#b88412;--open:#8a8f98;
  --claude:#c8692a;--codex:#1f7a8c;--human:#c2186e;
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --bg:#141417;--panel:#1d1d22;--ink:#ececf1;--muted:#9a9aa6;--line:#2c2c33;--accent:#7a97ff;
  --agreed:#4fc67c;--conceded:#a48cf0;--disputed:#f0624a;--atd:#e0a83a;--open:#8a8f98;
  --claude:#f08a4a;--codex:#4fb3c9;--human:#f05aa0;}}
:root[data-theme="dark"]{
  --bg:#141417;--panel:#1d1d22;--ink:#ececf1;--muted:#9a9aa6;--line:#2c2c33;--accent:#7a97ff;
  --agreed:#4fc67c;--conceded:#a48cf0;--disputed:#f0624a;--atd:#e0a83a;--open:#8a8f98;
  --claude:#f08a4a;--codex:#4fb3c9;--human:#f05aa0;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif}
header{padding:20px 16px 8px;max-width:1400px;margin:0 auto}
h1{font-size:20px;margin:0 0 6px;line-height:1.3}
h2{font-size:15px;margin:18px 0 8px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
h3{font-size:15px;margin:14px 0 6px}
.meta{color:var(--muted);font-size:13px}
.meta b{color:var(--ink);font-weight:600}
.wrap{max-width:1400px;margin:0 auto;padding:0 16px 40px;display:grid;grid-template-columns:minmax(0,1fr) minmax(320px,440px);gap:16px}
@media (max-width:900px){.wrap{grid-template-columns:1fr}}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.legend{display:flex;flex-wrap:wrap;gap:10px 16px;font-size:13px;margin:6px 0 10px}
.legend span::before{content:"";display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:6px;vertical-align:-1px;background:var(--c)}
.gridwrap{overflow-x:auto}
table.grid{border-collapse:separate;border-spacing:3px;font-size:13px}
table.grid th{font-weight:600;color:var(--muted);text-align:left;padding:2px 6px;white-space:nowrap}
table.grid th.r{text-align:center;cursor:pointer}
table.grid th.r:hover,table.grid th.r.sel{color:var(--accent)}
table.grid td.claim{max-width:360px;padding:2px 6px;cursor:pointer;vertical-align:middle}
table.grid td.claim .txt{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;line-height:1.3}
table.grid td.claim:hover,table.grid td.claim.sel{color:var(--accent)}
table.grid td.claim small{color:var(--muted)}
td.cell{width:46px;height:30px;border-radius:5px;cursor:pointer;background:var(--c);opacity:.85;position:relative;text-align:center;color:#fff;font-size:11px;font-weight:600}
td.cell:hover{opacity:1;outline:2px solid var(--accent)}
td.cell.sel{opacity:1;outline:2px solid var(--ink)}
td.cell.low{outline:2px dashed var(--human)}
td.cell.contested::before{content:"!";position:absolute;left:3px;top:1px;font-size:10px;font-weight:800;color:#fff}
td.cell.changed::after{content:"";position:absolute;right:3px;top:3px;width:6px;height:6px;border-radius:50%;background:#fff}
td.cell.none{background:transparent;cursor:default}
td.cell.verdict{background:var(--line);color:var(--ink);font-weight:500}
.bars{display:flex;gap:6px;align-items:flex-end;height:70px;margin:8px 0 2px}
.bar{flex:1;height:100%;display:flex;flex-direction:column-reverse;cursor:pointer;border-radius:4px;overflow:hidden;min-width:28px;background:var(--line)}
.bar div{width:100%}
.bar:hover{outline:2px solid var(--accent)}
.barlabels{display:flex;gap:6px;font-size:11px;color:var(--muted)}
.barlabels span{flex:1;text-align:center;min-width:28px}
.rounds{display:flex;flex-direction:column;gap:8px}
.round{border:1px solid var(--line);border-radius:8px;padding:8px 12px;cursor:pointer}
.round:hover,.round.sel{border-color:var(--accent)}
.round .t{font-weight:600;font-size:13px}
.round .s{color:var(--muted);font-size:13px}
.human{border-left:3px solid var(--human);padding:6px 10px;margin:6px 0;background:color-mix(in srgb,var(--human) 8%,transparent);border-radius:0 6px 6px 0;font-size:13px}
.human b{color:var(--human)}
.side{position:sticky;top:12px;max-height:calc(100vh - 24px);overflow:auto}
.tag{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11px;font-weight:600;color:#fff;background:var(--c);vertical-align:1px}
.who{font-weight:700}
.who.claude{color:var(--claude)}.who.codex{color:var(--codex)}
.block{border-top:1px solid var(--line);padding-top:10px;margin-top:10px}
.md{white-space:pre-wrap;overflow-wrap:anywhere}
.quiet{color:var(--muted);font-size:13px}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
details{margin:6px 0}summary{cursor:pointer;font-weight:600}
.srcs{font-size:12px;color:var(--muted);margin:4px 0 0 0;padding-left:16px}
button{font:inherit;font-size:13px;border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:6px;padding:3px 9px;cursor:pointer}
button:hover{border-color:var(--accent)}
.toolbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:4px 0 8px}
</style>
</head>
<body>
<header>
  <h1 id="title"></h1>
  <div class="meta" id="meta"></div>
</header>
<div class="wrap">
  <main>
    <section class="panel">
      <h2>How the ledger moved</h2>
      <div class="bars" id="bars"></div><div class="barlabels" id="barlabels"></div>
      <div class="legend">
        <span style="--c:var(--agreed)">agreed</span><span style="--c:var(--conceded)">conceded</span>
        <span style="--c:var(--disputed)">disputed</span><span style="--c:var(--atd)">agree to disagree</span>
        <span style="--c:var(--open)">open</span><span class="quiet">· dot = status changed this round</span><span class="quiet" id="judgeLegend" hidden>· faded = lower judge confidence · dashed = judge unsure (&lt;0.60) · ! = judge disagrees with the referee</span>
      </div>
      <div class="toolbar">
        <button id="onlyMoved">Show only claims that moved</button>
        <button id="showAll" hidden>Show all claims</button>
        <span class="quiet">Click a cell for that claim at that round, a round header for the whole round, a claim for its full history.</span>
      </div>
      <div class="gridwrap"><table class="grid" id="grid"></table></div>
    </section>
    <section class="panel">
      <h2>Rounds and interventions</h2>
      <div class="rounds" id="rounds"></div>
    </section>
    <section class="panel" id="synth"></section>
  </main>
  <aside class="panel side" id="side"><h2>Detail</h2><p class="quiet">Select something on the left.</p></aside>
</div>
<script>
const S = __DATA__;
const COLOR = {agreed:"var(--agreed)",conceded:"var(--conceded)",disputed:"var(--disputed)",agree_to_disagree:"var(--atd)",open:"var(--open)"};
const LABEL = {agreed:"agreed",conceded:"conceded",disputed:"disputed",agree_to_disagree:"agree to disagree",open:"open"};
const NAME = {claude:"Claude",codex:"Codex",both:"both"};
const esc = s => String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const safeUrl = u => /^https?:\/\//i.test(String(u??"")) ? u : "#";
const md = s => esc(s).replace(/\*\*(.+?)\*\*/g,"<b>$1</b>").replace(/(https?:\/\/[^\s)<\]]+)/g,'<a href="$1" target="_blank" rel="noopener">$1</a>');
const srcList = srcs => srcs && srcs.length ? `<ul class="srcs">${srcs.map(s=>`<li><a href="${esc(safeUrl(s.url||s))}" target="_blank" rel="noopener">${esc(s.title||s.url||s)}</a>${s.note?": "+esc(s.note):""}</li>`).join("")}</ul>` : "";
const tag = st => `<span class="tag" style="--c:${COLOR[st]||'var(--open)'}">${LABEL[st]||st}</span>`;
const pct = x => Math.round(x*100)+"%";
function judgeMd(j){
  if (!j) return "";
  const probs = o => Object.entries(o||{}).sort((a,b)=>b[1]-a[1]).map(([k,v])=>`${LABEL[k]||k} ${pct(v)}`).join(" · ");
  return `<div class="block"><b>Judge (decision model)</b>${j.contested?` <span class="tag" style="--c:var(--human)">disagrees${j.fed_back?", fed back":""}</span>`:""}
    <div class="quiet">Judge rules ${LABEL[j.status]||j.status} (${j.status_confidence.toFixed(2)})${j.contested?`, referee recorded ${LABEL[j.referee_status]||j.referee_status}`:""}: ${probs(j.status_probabilities)}</div>
    <div class="quiet">Stronger case: ${esc(j.lean)} (${j.lean_confidence.toFixed(2)}): ${probs(j.lean_probabilities)}</div>
    <div class="quiet">Moved: ${esc(j.moved)} · crux kind: ${esc(j.crux_kind)} · repeats: Claude ${pct(j.repeats.claude)}, Codex ${pct(j.repeats.codex)} · human needed ${pct(j.human_needed)}</div></div>`;
}

const rounds = S.rounds;
const claimIds = [];
const claimAt = {};  // id -> round -> ledger claim
for (const r of rounds) for (const c of r.ledger.claims) {
  if (!claimAt[c.id]) { claimAt[c.id] = {}; claimIds.push(c.id); }
  claimAt[c.id][r.round] = c;
}
const verdicts = {}; for (const v of (S.synthesis?.verdicts||[])) verdicts[v.claim_id] = v;
const finalLedger = rounds.length ? rounds[rounds.length-1].ledger : {claims:[]};
const finalClaim = {}; for (const c of finalLedger.claims) finalClaim[c.id] = c;
const humanAt = {}; // round -> [{kind,text}]
function parseAt(s){ const m = s.match(/^\((?:after round (\d+)|before the debate)/); return m ? (m[1]===undefined ? -1 : +m[1]) : -1; }
for (const f of S.facts) (humanAt[parseAt(f)] ||= []).push({kind:"fact", text:f});
for (const o of S.opinions) (humanAt[parseAt(o)] ||= []).push({kind:"opinion", text:o});

// header
const cfg = S.config;
document.getElementById("title").textContent = (S.code ? S.code+" — " : "") + S.topic;
document.title = (S.code||"Syzetetes") + " review";
document.getElementById("meta").innerHTML =
  `<b>Claude</b> ${esc(cfg.claude_model)} (${esc(cfg.claude_effort)}) · <b>Codex</b> ${esc(cfg.codex_model)} (${esc(cfg.codex_effort)}) · <b>Referee</b> ${esc(cfg.referee)} ${esc(cfg.referee_model)} · <b>Rounds</b> ${Math.max(0,...rounds.map(r=>r.round))} · <b>Ended</b> ${esc(S.stop_reason||"in progress")}` +
  (rounds.some(r=>r.ledger.judged_by) ? ` · <b>Judge</b> ${esc(rounds.filter(r=>r.ledger.judged_by).pop().ledger.judged_by)}` : "") +
  (S.derived_from ? ` · <b>Derived from</b> ${esc(S.derived_from)}` : "") +
  (S.context ? `<div style="margin-top:4px"><b>Starting context.</b> ${esc(S.context)}</div>` : "") +
  (S.sources.length ? `<div><b>Starting sources.</b> ${S.sources.map((s,i)=>`S${i+1}: `+(s.kind==="url"?`<a href="${esc(s.ref)}" target="_blank" rel="noopener">${esc(s.ref)}</a>`:esc(s.ref))).join(" · ")}</div>` : "") +
  (humanAt[-1] ? humanAt[-1].map(h=>`<div class="human"><b>${h.kind} (before the debate)</b> ${esc(h.text.replace(/^\([^)]*\)\s*/,""))}</div>`).join("") : "");

if (rounds.some(r => r.ledger.claims.some(c => c.judge))) document.getElementById("judgeLegend").hidden = false;

// bars
const order = ["agreed","conceded","agree_to_disagree","disputed","open"];
const bars = document.getElementById("bars"), bl = document.getElementById("barlabels");
for (const r of rounds) {
  const n = {}; for (const c of r.ledger.claims) n[c.status]=(n[c.status]||0)+1;
  const tot = r.ledger.claims.length || 1;
  const b = document.createElement("div"); b.className="bar"; b.title = `Round ${r.round}: `+order.filter(k=>n[k]).map(k=>`${n[k]} ${LABEL[k]}`).join(", ");
  b.innerHTML = order.map(k=>`<div style="height:${(n[k]||0)/tot*100}%;background:${COLOR[k]}"></div>`).join("");
  b.onclick = () => showRound(r.round);
  bars.appendChild(b);
  const l = document.createElement("span"); l.textContent = r.round===0?"open.":"R"+r.round; bl.appendChild(l);
}

// grid
let onlyMoved = false;
function moved(id){ const h = Object.values(claimAt[id]); return new Set(h.map(c=>c.status)).size>1; }
function buildGrid(){
  const g = document.getElementById("grid");
  const ids = claimIds.filter(id => !onlyMoved || moved(id));
  let h = `<tr><th>Claim</th>${rounds.map(r=>`<th class="r" data-r="${r.round}" title="Round ${r.round}">${r.round===0?"Open":"R"+r.round}</th>`).join("")}<th>Verdict</th></tr>`;
  for (const rawId of ids) {
    const id = esc(rawId);
    const fc = finalClaim[rawId] || Object.values(claimAt[rawId]).pop();
    h += `<tr><td class="claim" data-id="${id}"><small>${id} · ${NAME[fc.origin]||esc(fc.origin)}</small><div class="txt" title="${esc(fc.claim)}">${esc(fc.claim)}</div></td>`;
    let prev = null;
    for (const r of rounds) {
      const c = claimAt[rawId][r.round];
      if (!c) { h += `<td class="cell none"></td>`; continue; }
      const ch = prev && prev !== c.status ? " changed" : "";
      const conf = c.judge ? c.judge.status_confidence : null;
      const low = conf !== null && conf < 0.6 ? " low" : "";
      const con = c.judge && c.judge.contested ? " contested" : "";
      h += `<td class="cell${ch}${low}${con}" style="--c:${COLOR[c.status]}${conf!==null?`;opacity:${0.45+0.55*conf}`:""}" data-id="${id}" data-r="${r.round}" title="${id} after round ${r.round}: ${LABEL[c.status]}${conf!==null?` (judge confidence ${conf.toFixed(2)})`:""}">${c.status==="agree_to_disagree"?"ATD":c.status.slice(0,3)}</td>`;
      prev = c.status;
    }
    const v = verdicts[rawId];
    h += `<td class="cell verdict" data-id="${id}" data-r="verdict" title="${v?esc(v.headline):"no verdict"}">${v?"✓":"–"}</td></tr>`;
  }
  g.innerHTML = h;
  g.querySelectorAll("td.cell:not(.none)").forEach(td => td.onclick = () => td.dataset.r==="verdict" ? showClaim(td.dataset.id) : showCell(td.dataset.id, +td.dataset.r));
  g.querySelectorAll("td.claim").forEach(td => td.onclick = () => showClaim(td.dataset.id));
  g.querySelectorAll("th.r").forEach(th => th.onclick = () => showRound(+th.dataset.r));
}
buildGrid();
document.getElementById("onlyMoved").onclick = e => { onlyMoved = true; e.target.hidden = true; document.getElementById("showAll").hidden = false; buildGrid(); };
document.getElementById("showAll").onclick = e => { onlyMoved = false; e.target.hidden = true; document.getElementById("onlyMoved").hidden = false; buildGrid(); };

// round strip
const rs = document.getElementById("rounds");
for (const r of rounds) {
  const d = document.createElement("div"); d.className = "round"; d.dataset.r = r.round;
  const flags = (r.ledger.repetition_flags||[]).map(f=>`${f.claim_id} (${NAME[f.who]})`).join(", ");
  d.innerHTML = `<div class="t">${r.round===0?"Opening positions":"Round "+r.round}${r.first&&r.first!=="both"?` · ${NAME[r.first]} spoke first`:""}</div>
    <div class="s">${esc(r.ledger.round_summary)}</div>` +
    (flags ? `<div class="quiet">Repetition flagged: ${esc(flags)}</div>` : "") +
    (r.ledger.needs_human ? `<div class="quiet">Referee asked for a human decision: ${esc(r.ledger.human_question)}</div>` : "") +
    ((r.ledger.judge_notes||[]).length ? `<div class="quiet">Judge notes for the next round: ${r.ledger.judge_notes.map(esc).join(" · ")}</div>` : "");
  d.onclick = () => showRound(r.round);
  rs.appendChild(d);
  for (const h of (humanAt[r.round]||[])) {
    const hd = document.createElement("div"); hd.className = "human";
    hd.innerHTML = `<b>${h.kind} after round ${r.round}${/retrospectively/.test(h.text)?" (added retrospectively)":""}</b> ${esc(h.text.replace(/^\([^)]*\)\s*/,""))}`;
    rs.appendChild(hd);
  }
}

// synthesis
const syn = S.synthesis, sy = document.getElementById("synth");
sy.innerHTML = `<h2>Synthesis</h2>` + (syn ? `<div class="md">${md(syn.executive_summary)}</div>
  <div class="block"><h3>Strongest case for</h3><div class="md">${md(syn.strongest_case_for)}</div></div>
  <div class="block"><h3>Strongest case against</h3><div class="md">${md(syn.strongest_case_against)}</div></div>
  <div class="block"><h3>Guidance</h3><div class="md">${md(syn.what_the_author_should_do)}</div>${syn.caveats?.length?`<ul>${syn.caveats.map(c=>`<li>${md(c)}</li>`).join("")}</ul>`:""}</div>` : `<p class="quiet">Not written yet.</p>`) +
  (S.closings?.claude ? `<div class="block"><h3>Closing statements</h3>
    <details><summary><span class="who claude">Claude</span></summary><div class="md">${md(S.closings.claude.statement)}</div></details>
    <details><summary><span class="who codex">Codex</span></summary><div class="md">${md(S.closings.codex.statement)}</div></details></div>` : "") +
  (Object.keys(S.memos).length ? `<div class="block"><h3>Research briefings</h3>${Object.entries(S.memos).map(([w,m])=>`<details><summary><span class="who ${w}">${NAME[w]}</span></summary><div class="md">${md(m.summary)}</div><ul>${m.findings.map(f=>`<li>[${f.confidence}] ${md(f.finding)}${srcList(f.sources)}</li>`).join("")}</ul></details>`).join("")}</div>` : "");

// detail panel
const side = document.getElementById("side");
function select(sel){ document.querySelectorAll(".sel").forEach(e=>e.classList.remove("sel")); document.querySelectorAll(sel).forEach(e=>e.classList.add("sel")); }
function responsesFor(id, r){
  const out = [];
  for (const who of ["claude","codex"]) {
    const t = r.turns?.[who]; if (!t) continue;
    for (const resp of t.responses||[]) if (resp.claim_id===id)
      out.push(`<div class="block"><span class="who ${who}">${NAME[who]}</span> · <b>${esc(resp.stance.replace("_"," "))}</b>${resp.revised_claim?`<div class="quiet">Revised to: ${esc(resp.revised_claim)}</div>`:""}<div class="md">${md(resp.reasoning)}</div>${srcList(resp.sources)}</div>`);
    for (const nc of t.new_claims||[]) if (nc.claim && (claimAt[id][r.round]?.claim===nc.claim))
      out.push(`<div class="block"><span class="who ${who}">${NAME[who]}</span> · <b>introduced</b> (${esc(nc.confidence)})<div class="md">${md(nc.reasoning)}</div>${srcList(nc.sources)}</div>`);
    for (const er of t.evidence_requests||[]) if (er.claim_id===id)
      out.push(`<div class="block"><span class="who ${who}">${NAME[who]}</span> · <b>asked for evidence</b><div class="md">${md(er.what_would_change_my_mind)}</div></div>`);
  }
  return out.join("");
}
function showCell(id, rn){
  select(`td.cell[data-id="${CSS.escape(id)}"][data-r="${rn}"]`);
  const r = rounds.find(x=>x.round===rn), c = claimAt[id][rn];
  const prevRound = rounds.filter(x=>x.round<rn).pop(); const pc = prevRound && claimAt[id][prevRound.round];
  side.innerHTML = `<h2>${esc(id)} after ${rn===0?"the openings":"round "+rn}</h2>
    <p>${tag(c.status)}${pc&&pc.status!==c.status?` <span class="quiet">was ${LABEL[pc.status]}</span>`:""} <span class="quiet">· origin ${NAME[c.origin]}</span></p>
    <div class="md"><b>${esc(c.claim)}</b></div>
    ${pc&&pc.claim!==c.claim?`<div class="quiet">Previously worded: ${esc(pc.claim)}</div>`:""}
    <div class="block"><span class="who claude">Claude</span><div class="md">${md(c.claude_position)}</div></div>
    <div class="block"><span class="who codex">Codex</span><div class="md">${md(c.codex_position)}</div></div>
    ${c.crux?`<div class="block"><b>Crux</b><div class="md">${md(c.crux)}</div></div>`:""}
    ${judgeMd(c.judge)}
    ${srcList(c.sources)}
    <h3 style="margin-top:16px">What was said about it this round</h3>
    ${responsesFor(id, r) || `<p class="quiet">Neither side addressed it directly this round.</p>`}
    <p style="margin-top:12px"><button data-id="${esc(id)}" onclick="showClaim(this.dataset.id)">Full history of ${esc(id)}</button> <button onclick="showRound(${rn})">Whole round ${rn}</button></p>`;
  side.scrollTop = 0;
}
function showClaim(id){
  select(`td.claim[data-id="${CSS.escape(id)}"]`);
  const v = verdicts[id];
  let h = `<h2>${esc(id)} · history</h2>`;
  if (v) h += `<div class="md"><b>${esc(v.headline)}</b></div><div class="md">${md(v.explanation)}</div>`;
  let prev = null;
  for (const r of rounds) {
    const c = claimAt[id][r.round]; if (!c) continue;
    const changed = prev && prev.status!==c.status;
    h += `<div class="block"><b>${r.round===0?"Opening":"Round "+r.round}</b> ${tag(c.status)}${changed?` <span class="quiet">changed from ${LABEL[prev.status]}</span>`:""}
      ${prev&&prev.claim!==c.claim?`<div class="quiet">Reworded: ${esc(c.claim)}</div>`:""}
      ${c.crux?`<div class="quiet">Crux: ${esc(c.crux)}</div>`:""}
      ${c.judge?`<div class="quiet">Judge: ${c.judge.contested?`<b>disagrees, rules ${LABEL[c.judge.status]||c.judge.status}</b>`:"agrees"} (${c.judge.status_confidence.toFixed(2)}), lean ${esc(c.judge.lean)} (${c.judge.lean_confidence.toFixed(2)}), moved ${esc(c.judge.moved)}</div>`:""}
      ${responsesFor(id, r)}
      <p><button data-id="${esc(id)}" data-r="${r.round}" onclick="showCell(this.dataset.id,+this.dataset.r)">Positions after round ${r.round}</button></p></div>`;
    prev = c;
  }
  side.innerHTML = h; side.scrollTop = 0;
}
function showRound(rn){
  select(`th.r[data-r="${rn}"], .round[data-r="${rn}"]`);
  const r = rounds.find(x=>x.round===rn);
  const who = r.first==="both" ? ["claude","codex"] : (r.first==="codex" ? ["codex","claude"] : ["claude","codex"]);
  let h = `<h2>${rn===0?"Opening positions":"Round "+rn}</h2><div class="md">${md(r.ledger.round_summary)}</div>`;
  for (const w of who) {
    const t = r.turns?.[w]; if (!t) continue;
    h += `<div class="block"><details ${rn===0?"":"open"}><summary><span class="who ${w}">${NAME[w]}</span>${t.nothing_new?' <span class="quiet">(nothing new)</span>':""}</summary><div class="md">${md(t.argument)}</div></details>
      ${t.responses?.length?`<div class="quiet">Stances: ${t.responses.map(x=>`<a href="#" data-id="${esc(x.claim_id)}" data-r="${rn}" onclick="showCell(this.dataset.id,+this.dataset.r);return false">${esc(x.claim_id)}</a> ${esc(x.stance.replace("_"," "))}`).join(" · ")}</div>`:""}
      ${t.new_claims?.length?`<div class="quiet">New claims: ${t.new_claims.length}</div>`:""}</div>`;
  }
  const nudges = ["claude","codex"].filter(w=>r.ledger["nudge_"+w]).map(w=>`<div><span class="who ${w}">${NAME[w]}</span>: ${esc(r.ledger["nudge_"+w])}</div>`).join("");
  if (nudges) h += `<div class="block"><b>Referee nudges for next round</b>${nudges}</div>`;
  for (const hu of (humanAt[rn]||[])) h += `<div class="human"><b>${hu.kind}</b> ${esc(hu.text.replace(/^\([^)]*\)\s*/,""))}</div>`;
  side.innerHTML = h; side.scrollTop = 0;
}
</script>
</body>
</html>
"""
