# debate

Two AI models research a topic, argue it out in structured rounds, and hand you a referenced
Markdown report of what they agreed on, what they still dispute, and why.

- **Claude** runs through the Claude Code CLI on your Claude subscription.
- **Codex** runs through the Codex CLI on your ChatGPT subscription.
- No API keys. Nothing is sent anywhere except through those two CLIs.

## How a run works

1. **Research.** Both models independently search the web and write a cited briefing. Briefings are shared.
2. **Opening positions.** Each states a thesis and falsifiable claims with sources.
3. **Rounds.** Debaters alternate (who speaks first flips each round). Every turn must answer the other
   side's claims by ID with one stance each: accept, maintain (with a *new* argument), revise, or
   agree to disagree. After each round a **referee** (bookkeeping only, never argues) updates the claim
   ledger, flags repetition, and nudges a side that is restating itself.
4. **Termination.** The debate ends when every claim is settled, when both sides say they have nothing
   new, when the ledger has not moved for `stable_rounds` rounds, or at the round cap.
5. **Human checkpoints.** The run pauses and asks you when the referee hits something the models cannot
   resolve alone (conflicting sources, a value judgement, a scope question, a stall), or whenever your
   pause policy says so (see below). At a checkpoint you can type:
   - `continue` or `stop`, or `extend 3` at the round cap;
   - `opinion: <your view>`: not binding. Both debaters must engage with it and may disagree, with reasons.
   - anything else: a binding ruling (a veto). Both debaters treat it as settled and the debate changes course.
6. **Closing and synthesis.** Each side writes a closing statement. The referee model writes the
   executive summary, per-claim verdicts, the strongest case for and against, and guidance for you.
7. **Report.** `<code>-02-report.md` with every argument, the agreed / conceded / disputed / agree-to-disagree
   points, closing statements, research briefings, the full round-by-round transcript, and a numbered
   reference list. Inline URLs are replaced by `[n]` markers.

While it runs, `<code>-01-transcript.md` in the run folder is appended live so you can read along.

## Giving the debate a starting point

Optional. Anything you give here complements the topic: both sides start from it, but must still check
it against independent evidence.

```
--note "I am writing for engineers."        # short inline context
--context notes.md                           # a file of context (repeatable; '-' for stdin)
--source https://example.org/paper           # a URL both sides must read and cite (repeatable)
--source ~/papers/jones-2022.txt             # a local file; its text is embedded (up to 40k chars)
--opinion "I lean towards X."                # your bias, stated as such (see below)
```

Sources are numbered S1, S2, ... in the prompts and listed in the report. `debate rerun D0001 --source ...`
adds sources to a finished run; research and openings are redone since the briefings must start from them.

## Steering the debate with your own opinion

Two kinds of input, both recorded in the report:

| | effect |
|---|---|
| **opinion** | Non-binding. Debaters and referee see "the human currently thinks X" and must argue with it, not defer to it. |
| **ruling** | Binding (a veto). Treated as settled; debaters stop arguing it and the course changes. |

**Up front**, when starting a run:

```
.venv/bin/debate run "..." --opinion "I suspect pensions are the real issue, not fertility."
.venv/bin/debate run "..." --ruling "Ignore climate arguments; scope is economics only."
```

**During the run**, choose when it pauses for you:

```
--pause referee     # default: only when the referee asks or the ledger stalls
--pause disputes    # after every round that still has a disputed claim: you decide how to tie it
--pause always      # after every round
--pause never       # same as --unattended
--pause-when "disputed >= 2 and round >= 2"   # any expression over round, disputed, open, agreed,
                                              # conceded, agree_to_disagree, total, unchanged
```

**Retrospectively**, after a run is done, inject an opinion or ruling and re-run from a chosen point.
A new coded run is created; the research (and the rounds you keep) are inherited, the rest is redone:

```
.venv/bin/debate rerun D0001 --opinion "I think the Ponzi framing is right."        # redo from after the openings
.venv/bin/debate rerun D0001 --keep-rounds 2 --ruling "Treat K4 as settled for Codex." # keep rounds 0-2, redo from 3
.venv/bin/debate rerun D0001 --redo-openings --opinion "..."                          # keep research only
.venv/bin/debate rerun D0001 --keep-rounds 1 --pause disputes                          # and change the pause policy
```

## Run folders and codes

Every run gets a sequential code, `D0001`, `D0002`, ... The code is the handle for every other command.

```
debates/
  D0001-is-remote-work-net-positive-for-early-stage/
    D0001.json               state (resumable)
    D0001-01-transcript.md   live log
    D0001-02-report.md       final referenced report
    D0001-03-chat.md         Q&A log, written by `debate chat`
```

## Ask questions about a finished debate

```
.venv/bin/debate chat D0001                       # interactive
.venv/bin/debate chat D0001 "Which claims stayed disputed and why?"
```

Answers are grounded on the report text only: the whole report is put in the prompt, the model is told
to answer from it or say the debate does not cover the question, and every answer carries verbatim
excerpts. It uses the smallest Claude model (haiku), effort low, extended thinking disabled, no tools
and no web. Neither CLI exposes a sampling temperature, so this is as deterministic as they allow.
Each session is appended to `D0001-03-chat.md`.

## Install

```
cd debate
python3 -m venv .venv && .venv/bin/pip install -e .
```

Requires `claude` and `codex` on your PATH, both logged in (`claude` and `codex login`).

## Use

```
.venv/bin/debate run "Is remote work net positive for early-stage startups?"
.venv/bin/debate run "..." --context notes.md --note "I am writing a 2000-word essay for engineers."
.venv/bin/debate run "..." --claude-model opus --claude-effort xhigh --codex-effort high --max-rounds 10
.venv/bin/debate run "..." --referee codex --referee-model gpt-6.1-sol    # let Codex referee instead
.venv/bin/debate list
.venv/bin/debate resume D0003
.venv/bin/debate chat D0003
.venv/bin/debate config
```

Ctrl-C at any time; `debate resume <code>` picks up from the last saved step.

## Configuration

Defaults can be set in `~/.config/debate/config.toml` (any field of `debate/config.py:Config`):

```toml
claude_model = "opus"
claude_effort = "high"
codex_model = "gpt-6.1-sol"     # defaults to the model in ~/.codex/config.toml
codex_effort = "high"
referee = "claude"
referee_model = "sonnet"
max_rounds = 8
stable_rounds = 2
```

CLI flags override the file.

## Design notes

- Each model call is single-shot with the full needed context in the prompt. There is no CLI session
  state, so a crash loses at most one call.
- Both CLIs run isolated from your personal settings: no MCP servers, plugins, hooks, CLAUDE.md or
  AGENTS.md. Codex runs read-only in a temp dir.
- Structured output is enforced by each CLI's JSON-schema mode and re-validated locally; a malformed
  answer is sent back with the validation errors and re-asked.
- The ledger is the source of truth. The report's verdict sections are rendered from it, not from
  free prose, and a referee that drops a claim has it restored automatically.
- The referee model can be either CLI. If you worry about Claude refereeing a Claude-vs-Codex debate,
  run with `--referee codex` and compare.

## Tests

```
.venv/bin/pip install pytest && .venv/bin/python -m pytest -q
```

Tests use scripted fake agents; no CLIs or network needed.
