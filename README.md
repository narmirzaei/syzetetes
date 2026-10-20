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
5. **Human checkpoints.** When the referee hits something the models cannot resolve alone (conflicting
   sources, a value judgement, a scope question, a stall) the run pauses and asks you. You can type
   `continue`, `stop`, `extend 3`, or a ruling in plain words that both debaters then treat as binding.
   `--unattended` disables this.
6. **Closing and synthesis.** Each side writes a closing statement. The referee model writes the
   executive summary, per-claim verdicts, the strongest case for and against, and guidance for you.
7. **Report.** `report.md` with every argument, the agreed / conceded / disputed / agree-to-disagree
   points, closing statements, research briefings, the full round-by-round transcript, and a numbered
   reference list. Inline URLs are replaced by `[n]` markers.

While it runs, `transcript.md` in the run folder is appended live so you can read along.

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
.venv/bin/debate resume debates/20261020-1530-is-remote-work-net-positive
.venv/bin/debate config
```

Ctrl-C at any time; `debate resume <run dir>` picks up from the last saved step.

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
