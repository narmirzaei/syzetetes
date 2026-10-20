# Syzetetes

*Syzetetes* (Greek συζητητής, "one who investigates together") makes two different AI models research a
question, argue it out in structured rounds under a bookkeeping referee, and hand you a referenced
Markdown report of what they agreed on, what they still dispute, and why. You can seed it with your own
context, sources and opinions, steer it while it runs, re-run it with hindsight, and afterwards ask
questions that are answered only from what the debate produced. An interactive review page shows how every
claim moved, round by round, until the synthesis.

- **Claude** runs through the [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI on your Claude subscription.
- **Codex** runs through the [Codex](https://github.com/openai/codex) CLI on your ChatGPT subscription.
- No API keys and no third-party services. Nothing leaves your machine except through those two CLIs.
- Zero Python dependencies. Python 3.11+.

See [example-report.md](example-report.md) for what a finished report looks like.

## Why two models

A single model asked to "consider both sides" tends to produce a tidy, agreeable survey. Two models with
different training, forced to answer each other's claims one by one with sources, under a referee that
only keeps the books, produce something closer to a real argument: concessions with reasons, disputes
narrowed to their crux, and an honest list of what nobody could settle.

## How a run works

1. **Research.** Both models independently search the web and write a cited briefing. Briefings are shared.
2. **Opening positions.** Each states a thesis and falsifiable claims with sources.
3. **Rounds.** Debaters alternate (who speaks first flips each round). Every turn must answer the other
   side's claims by ID with one stance each: accept, maintain (with a *new* argument), revise, or agree to
   disagree. After each round a **referee** (bookkeeping only, never argues) updates the claim ledger, flags
   repetition, and nudges a side that is restating itself.
4. **Termination.** The debate ends when every claim is settled, when both sides say they have nothing new,
   when the ledger has not moved for `stable_rounds` rounds, or at the round cap.
5. **Human checkpoints.** The run pauses and asks you when the referee hits something the models cannot
   resolve alone, or whenever your pause policy says so. You can let it continue, stop it, give your
   opinion, or issue a binding fact. See [Steering](#steering-the-debate-with-your-own-opinion).
6. **Closing and synthesis.** Each side writes a closing statement. The referee model writes the executive
   summary, per-claim verdicts, the strongest case for and against, and guidance for you.
7. **Report.** Every argument, the agreed / conceded / disputed / agree-to-disagree points, closing
   statements, research briefings, the full round-by-round transcript, and a numbered reference list.

While it runs, the transcript file in the run folder is appended live so you can read along.

## Install

```
git clone https://github.com/narmirzaei/syzetetes
cd syzetetes
python3 -m venv .venv && .venv/bin/pip install -e .
```

Requires `claude` and `codex` on your PATH, both logged in (`claude` and `codex login`).

## Quick start

```
.venv/bin/syzetetes run "Is remote work net positive for early-stage startups?"
.venv/bin/syzetetes list
.venv/bin/syzetetes review D0001      # interactive page: how the synthesis was reached
.venv/bin/syzetetes chat D0001        # ask questions, answered only from the report
```

More options:

```
syzetetes run "..." --context notes.md --note "I am writing a 2000-word essay for engineers."
syzetetes run "..." --claude-model opus --claude-effort xhigh --codex-effort high --max-rounds 10
syzetetes run "..." --referee codex --referee-model gpt-6.1-sol    # let Codex referee instead
syzetetes resume D0003
syzetetes config
```

Ctrl-C at any time; `syzetetes resume <code>` picks up from the last saved step.

## What it costs

Every model call is a `claude -p` or `codex exec` subprocess, so usage lands on your two subscriptions,
never on an API bill. A default run (Opus high, Codex high, Sonnet referee, up to 8 rounds, web research
on) is roughly 30 to 35 model calls, each carrying the growing transcript. Expect a noticeable dent in
both weekly quotas. For a cheap first try: `--claude-model sonnet --max-rounds 2 --no-research`.

## Run folders and codes

Every run gets a sequential code, `D0001`, `D0002`, ... The code is the handle for every other command.

```
debates/
  D0001-is-remote-work-net-positive-for-early-stage/
    D0001.json               state (resumable)
    D0001-01-transcript.md   live log
    D0001-02-report.md       final referenced report
    D0001-03-chat.md         Q&A log, written by `syzetetes chat`
    D0001-04-review.html     interactive review, written at the end of a run and by `syzetetes review`
```

`resume`, `render`, `chat` and `rerun` accept the code (`D0001`, or just `d1`) or a path to the folder.

## Giving the debate a starting point

Optional. Anything you give here complements the question: both sides start from it, but must still check
it against independent evidence.

```
--note "I am writing for engineers."        # short inline context
--context notes.md                           # a file of context (repeatable; '-' for stdin)
--source https://example.org/paper           # a URL both sides must read and cite (repeatable)
--source ~/papers/jones-2022.txt             # a local file; its text is embedded (up to 40k chars)
--opinion "I lean towards X."                # your bias, stated as such (see below)
```

Sources are numbered S1, S2, ... in the prompts and listed in the report. `syzetetes rerun D0001 --source ...`
adds sources to a finished run; research and openings are redone since the briefings must start from them.

## Steering the debate with your own opinion

Two kinds of input, both recorded in the report and shown to the debaters, the referee and the synthesis:

| | effect |
|---|---|
| **opinion** | Not binding. Debaters and referee see "the human currently thinks X" and must engage with it: agree if the evidence supports it, say why if it does not. They are told not to defer to it or flatter it. |
| **fact** | Binding. Treated as true for this debate: debaters build on it, stop arguing against it, and the course of the debate changes. |

Either can be given at three moments: before the debate, at a pause in the middle, or retrospectively
at any round of a finished debate (which replays the rest and produces a new version).

**Up front**, when starting a run:

```
syzetetes run "..." --opinion "I suspect pensions are the real issue, not fertility."
syzetetes run "..." --fact "Ignore climate arguments; scope is economics only."
```

**During the run**, at any checkpoint, type `continue`, `stop`, `extend 3` (at the round cap),
`opinion: <your view>` or `fact: <statement>`. The debate then continues with it. Choose when it pauses:

```
--pause referee     # default: only when the referee asks or the ledger stalls
--pause disputes    # after every round that still has a disputed claim: you decide how to tie it
--pause always      # after every round
--pause never       # same as --unattended; deadlocks become agree-to-disagree
--pause-when "disputed >= 2 and round >= 2"   # any expression over round, disputed, open, agreed,
                                              # conceded, agree_to_disagree, total, unchanged
```

**Retrospectively**, after a run is done, inject an opinion or fact at any round and replay from there.
A new coded run is created; the research and the rounds before the injection point are inherited, the
rest is replayed, and the report says which run it was derived from:

```
syzetetes rerun D0001 --opinion "I think the Ponzi framing is right."         # inject after the openings, replay rounds
syzetetes rerun D0001 --keep-rounds 2 --fact "Korea's 2024 TFR was 0.75."     # inject after round 2, replay from 3
syzetetes rerun D0001 --redo-openings --opinion "..."                          # inject before the openings
syzetetes rerun D0001 --keep-rounds 1 --pause disputes                         # replay from round 2 with a new pause policy
```

## Reviewing how the synthesis was reached

```
syzetetes review D0001            # writes D0001-04-review.html and opens it
```

A single self-contained HTML page, no network needed:

- a stacked bar per round showing the ledger's status mix moving toward settlement;
- a claim-by-round grid, colour-coded, with a dot wherever a status changed. Click a cell to see both
  sides' positions and the crux at that round, plus each debater's stance and reasoning on that claim
  that round and the sources they cited. Click a claim for its full history and the synthesis verdict,
  or a round header for the full arguments, referee nudges and repetition flags;
- the round strip with the referee's summaries and every human intervention in place;
- the executive summary, strongest cases, guidance, closing statements and research briefings.

"Show only claims that moved" filters the grid to the claims whose status changed.

## Asking questions about a finished debate

```
syzetetes chat D0001                       # interactive
syzetetes chat D0001 "Which claims stayed disputed and why?"
```

Answers are grounded on the report text only: the whole report is put in the prompt, the model is told
to answer from it or say the debate does not cover the question, and every answer carries verbatim
excerpts. It uses the smallest Claude model (haiku), effort low, extended thinking disabled, no tools
and no web. Neither CLI exposes a sampling temperature, so this is as deterministic as they allow.
Each session is appended to the run's chat log.

## Configuration

Defaults can be set in `~/.config/syzetetes/config.toml` (any field of `syzetetes/config.py:Config`):

```toml
claude_model = "opus"
claude_effort = "high"
codex_model = "gpt-6.1-sol"     # defaults to the model in ~/.codex/config.toml
codex_effort = "high"
referee = "claude"
referee_model = "sonnet"
max_rounds = 8
stable_rounds = 2
pause = "referee"
out_dir = "debates"
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
- Human input is typed: opinions and facts are stored separately, rendered separately in every prompt,
  and labelled in the report, so a reader can always tell what the models concluded on their own.

## Layout

```
syzetetes/
  cli.py       commands: run, resume, rerun, review, chat, list, render, config
  engine.py    phases, ledger, termination, checkpoints, derive (rerun)
  agents.py    subprocess wrappers for the Claude Code and Codex CLIs
  prompts.py   every prompt; debaters are symmetric
  schemas.py   JSON schemas and a small validator
  report.py    Markdown report with numbered references
  runs.py      run codes, folder layout, source loading
  chat.py      grounded Q&A over a finished report
  review.py    interactive HTML review of the ledger's evolution
  config.py    defaults, user config file, CLI overrides
tests/         scripted fake agents; no CLIs or network needed
```

## Tests

```
.venv/bin/pip install pytest && .venv/bin/python -m pytest -q
```

## Contributing

Issues and pull requests are welcome. Keep the debaters symmetric (the only difference between Claude's
and Codex's prompts should be who they are told they are), keep the ledger as the single source of truth,
and add a fake-agent test for any change to the engine.

## License

[MIT](LICENSE).
