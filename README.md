# Syzetetes

*Syzetetes* (Greek συζητητής, "one who investigates together") makes two different AI models research a
question, argue it out in structured rounds under a bookkeeping referee, and hand you a referenced report
of what they agreed on, what they still dispute, and why. You can seed it with your own context, sources,
opinions and facts; steer it while it runs; replay it with hindsight; review visually how every claim
moved; and afterwards ask questions that are answered only from what the debate produced.

- **Claude** runs through the [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI on your Claude subscription.
- **Codex** runs through the [Codex](https://github.com/openai/codex) CLI on your ChatGPT subscription.
- No API keys and no third-party services. Nothing leaves your machine except through those two CLIs.
- Zero Python dependencies. Python 3.11+.

See [example-report.md](example-report.md) for a finished report and [examples/](examples/) for ready-made specs.

## Contents

- [Why two models](#why-two-models)
- [Install](#install)
- [Five-minute tour](#five-minute-tour)
- [How a run works](#how-a-run-works)
- [The spec file](#the-spec-file)
- [Recipes](#recipes)
  - [Cheapest possible run](#cheapest-possible-run)
  - [Give it your context and sources](#give-it-your-context-and-sources)
  - [Tell it what you think](#tell-it-what-you-think)
  - [Establish a fact it must not argue with](#establish-a-fact-it-must-not-argue-with)
  - [Moderate it yourself as it runs](#moderate-it-yourself-as-it-runs)
  - [Pause only when something specific happens](#pause-only-when-something-specific-happens)
  - [Replay a finished debate with hindsight](#replay-a-finished-debate-with-hindsight)
  - [Let Codex referee](#let-codex-referee)
  - [Review how the synthesis was reached](#review-how-the-synthesis-was-reached)
  - [Interrogate the result](#interrogate-the-result)
  - [Reproduce a run](#reproduce-a-run)
- [Run folders and codes](#run-folders-and-codes)
- [Commands](#commands)
- [What it costs](#what-it-costs)
- [Configuration defaults](#configuration-defaults)
- [Design notes](#design-notes)
- [Layout, tests, contributing, license](#layout)

## Why two models

A single model asked to "consider both sides" tends to produce a tidy, agreeable survey. Two models with
different training, forced to answer each other's claims one by one with sources, under a referee that
only keeps the books, produce something closer to a real argument: concessions with reasons, disputes
narrowed to their crux, and an honest list of what nobody could settle.

## Install

```
git clone https://github.com/narmirzaei/syzetetes
cd syzetetes
python3 -m venv .venv && .venv/bin/pip install -e .
```

Requires `claude` and `codex` on your PATH, both logged in (`claude` and `codex login`). The examples
below assume `.venv/bin` is on your PATH, or prefix each command with `.venv/bin/`.

## Five-minute tour

```
syzetetes init                 # writes syzetetes.toml, a commented template
$EDITOR syzetetes.toml         # fill in 'topic'; everything else is optional
syzetetes run syzetetes.toml   # research → openings → rounds → closings → synthesis → report
syzetetes review D0001         # interactive page: how every claim moved until the synthesis
syzetetes chat D0001           # ask questions, answered only from the report
syzetetes list                 # every run, its code and status
```

No spec file needed for a quick one:

```
syzetetes run "Is remote work net positive for early-stage startups?"
```

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
   resolve alone, or whenever your pause policy says so. You can let it continue, stop it, give an
   opinion, or establish a fact.
6. **Closing and synthesis.** Each side writes a closing statement. The referee model writes the executive
   summary, per-claim verdicts, the strongest case for and against, and guidance for you.
7. **Report and review.** A Markdown report with every argument, the agreed / conceded / disputed /
   agree-to-disagree points, closing statements, briefings, the full transcript and a numbered reference
   list; and an interactive HTML review of how the ledger moved.

While it runs, the transcript file in the run folder is appended live so you can read along.

## The spec file

Everything a run needs lives in one TOML file. `syzetetes init` writes a commented template; every key is
optional except `topic`, and every CLI flag has a key here. A flag given on the command line overrides the
file. (TOML rather than YAML because Python reads it with no third-party dependency, and it has comments.)

```toml
topic = "Is sub-replacement fertility a serious problem, or is the pension 'Ponzi' concern a fixable design flaw?"

# starting point, all optional
note = "I am evaluating an economist's claim that fewer babies is not a problem."
context_files = ["notes.md"]                       # text handed to both sides as context
sources = ["https://example.org/paper", "~/papers/jones-2022.txt"]   # both sides must read, cite, check
opinions = ["I suspect pensions are the real issue, not fertility."]   # not binding; they must engage with it
facts = ["Scope is economics only; ignore climate arguments."]         # binding; treated as true

[models]
claude_model = "opus"        # opus | sonnet | haiku | fable | full model id
claude_effort = "high"       # low | medium | high | xhigh | max
codex_model = "gpt-6.1-sol"  # whatever your ChatGPT plan allows; defaults to ~/.codex/config.toml
codex_effort = "high"
referee = "claude"           # claude | codex
referee_model = "sonnet"
referee_effort = "medium"

[debate]
max_rounds = 8
stable_rounds = 2            # stop after this many rounds with no status change
research = true
pause = "referee"            # never | referee | disputes | always
pause_when = ""              # e.g. "disputed >= 2 and round >= 2"
out_dir = "debates"
timeout_s = 1800
retries = 3

# [rerun]                    # replay a finished run instead of starting fresh
# from = "D0001"
# keep_rounds = 2
# redo_openings = false
```

Paths in `context_files` and `sources` resolve relative to the spec file. Every run also saves the
effective spec it ran with as `<code>-00-spec.toml`, so any run can be reproduced or used as a template.

## Recipes

Each recipe shows the spec form and the equivalent flags. The files under [examples/](examples/) are
runnable as they are: `syzetetes run examples/cheap-smoke-test.toml`.

### Cheapest possible run

Check both CLIs work before spending real quota. [examples/cheap-smoke-test.toml](examples/cheap-smoke-test.toml)

```toml
topic = "Tabs or spaces for Python?"
[models]
claude_model = "haiku"
claude_effort = "low"
codex_effort = "low"
referee_model = "haiku"
referee_effort = "low"
[debate]
max_rounds = 1
research = false
pause = "never"
```

```
syzetetes run "Tabs or spaces for Python?" --claude-model haiku --claude-effort low --codex-effort low \
  --referee-model haiku --referee-effort low --max-rounds 1 --no-research --pause never
```

### Give it your context and sources

Anything you give here complements the question: both sides start from it but must check it against
independent evidence. Sources are numbered S1, S2, ... in the prompts and listed in the report.
[examples/with-starting-point.toml](examples/with-starting-point.toml)

```toml
topic = "Should a solo founder write product documentation before writing any code?"
note = "I am a solo technical founder with 6 months of runway. I want a rule I can actually follow."
context_files = ["my-notes.md"]
sources = [
  "https://tom.preston-werner.com/2010/08/23/readme-driven-development.html",
  "~/papers/working-backwards.txt",       # a local file: its text is embedded (up to 40k chars)
]
```

```
syzetetes run "Should a solo founder ..." --note "I am a solo technical founder ..." \
  --context my-notes.md --source https://tom.preston-werner.com/... --source ~/papers/working-backwards.txt
```

`--context -` reads context from stdin, so you can pipe a document in.

### Tell it what you think

An **opinion** is your bias, stated as such. It is not binding: the debaters and the referee are told the
human currently thinks this, must engage with it (agree if the evidence supports it, say why if not), and
must not defer to it or flatter it. The report labels it as yours.

```toml
opinions = ["I suspect docs-first only pays off once there is a second person on the team."]
```

```
syzetetes run "..." --opinion "I suspect docs-first only pays off once there is a second person on the team."
```

### Establish a fact it must not argue with

A **fact** is binding. It is treated as true for this debate: both sides build on it and stop arguing
against it, which changes the course of the debate. Use it for scope decisions, for data you trust more
than what the models find, or to veto a line of argument.

```toml
facts = [
  "Assume the product is a developer tool with an API; consumer apps are out of scope.",
  "Korea's 2024 total fertility rate was 0.75 (Statistics Korea, February 2025).",
]
```

```
syzetetes run "..." --fact "Assume the product is a developer tool with an API; consumer apps are out of scope."
```

Opinions and facts can be given at three moments: before the debate (as above), at a pause in the middle
(next recipe), or retrospectively at any round of a finished debate (replay recipe).

### Moderate it yourself as it runs

Choose when the debate pauses for you. [examples/hands-on-moderation.toml](examples/hands-on-moderation.toml)

| `pause =` | pauses |
|---|---|
| `"referee"` (default) | when the referee asks for a decision, or the ledger has not moved for `stable_rounds` rounds |
| `"disputes"` | after every round that still has a disputed claim: you tie-break every disagreement |
| `"always"` | after every round |
| `"never"` | never (same as `--unattended`); deadlocks become agree-to-disagree |

At a checkpoint you see the open disputes and type one of:

```
continue                 carry on
stop                     end the debate now; closings and synthesis still run
extend 2                 at the round cap: allow two more rounds
opinion: <your view>     recorded as your opinion; the debate continues with it
fact: <statement>        recorded as a binding fact; the debate continues with it
```

```
syzetetes run "Is remote work net positive for early-stage startups?" --pause disputes
```

### Pause only when something specific happens

`pause_when` is an expression over the ledger, checked after every round in addition to `pause`:

```toml
[debate]
pause = "referee"
pause_when = "disputed >= 2 and round >= 2"
```

Names available: `round`, `disputed`, `open`, `agreed`, `conceded`, `agree_to_disagree`, `total`, and
`unchanged` (rounds in a row with no status change). Examples:

```
pause_when = "agree_to_disagree >= 1"          # someone wants to give up on a claim: let me weigh in first
pause_when = "unchanged >= 1 and disputed > 0" # it is starting to stall
pause_when = "round == 3"                      # check in once, mid-debate
```

### Replay a finished debate with hindsight

Inject an opinion or fact at any round and replay from there. A new coded run is created; research and
the rounds before the injection point are inherited, the rest is redone, and the report records which run
it derived from. The original is untouched. [examples/replay-with-a-fact.toml](examples/replay-with-a-fact.toml)

```toml
facts = ["Korea's 2024 total fertility rate was 0.75 (Statistics Korea, February 2025)."]
opinions = ["I think both of you are too quick to call the pension problem 'fixable'."]
[rerun]
from = "D0001"
keep_rounds = 2          # inherit openings and rounds 1-2; inject after round 2; replay from round 3
[debate]
pause = "disputes"       # and moderate the replay yourself
```

```
syzetetes rerun D0001 --keep-rounds 2 --fact "Korea's 2024 TFR was 0.75." --pause disputes
syzetetes rerun D0001 --opinion "..."                     # inject after the openings, replay all rounds
syzetetes rerun D0001 --redo-openings --opinion "..."     # inject before the openings; keep only research
syzetetes rerun D0001 --source https://new-paper.org      # new sources: research is redone too
syzetetes rerun D0001 --keep-rounds 3 --claude-model fable --max-rounds 10   # change models or shape
```

### Let Codex referee

If you worry about Claude refereeing a Claude-vs-Codex debate, swap the referee and compare the two
reports. [examples/codex-referees.toml](examples/codex-referees.toml)

```toml
[models]
referee = "codex"
referee_model = "gpt-6.1-sol"
```

```
syzetetes run "..." --referee codex --referee-model gpt-6.1-sol
```

### Review how the synthesis was reached

```
syzetetes review D0001            # writes D0001-04-review.html and opens it
```

A single self-contained page, no network needed:

- a stacked bar per round showing the ledger's status mix moving toward settlement;
- a claim-by-round grid, colour-coded, with a dot wherever a status changed. Click a cell for both sides'
  positions and the crux at that round, each debater's stance and reasoning on that claim, and the sources
  cited. Click a claim for its full history ending in the synthesis verdict. Click a round header for the
  full arguments, referee nudges and repetition flags;
- the round strip with the referee's summaries and every human intervention in place;
- the executive summary, strongest cases, guidance, closing statements and research briefings.

"Show only claims that moved" filters the grid to claims whose status changed.

### Interrogate the result

```
syzetetes chat D0001                                       # interactive; blank line to quit
syzetetes chat D0001 "Which claims stayed disputed and why?"
syzetetes chat D0001 "What did Codex concede in round 2?" | jq .     # JSON when piped
```

Answers are grounded on the report text only: the whole report is put in the prompt, the model is told
to answer from it or say the debate does not cover the question, and every answer carries verbatim
excerpts. It uses the smallest Claude model (haiku), effort low, extended thinking disabled, no tools and
no web. Neither CLI exposes a sampling temperature, so this is as deterministic as they allow. Each
session is appended to the run's chat log.

### Reproduce a run

```
syzetetes run debates/D0001-*/D0001-00-spec.toml                 # same inputs and settings, new code
cp debates/D0001-*/D0001-00-spec.toml variant.toml && $EDITOR variant.toml
```

## Run folders and codes

Every run gets a sequential code, `D0001`, `D0002`, ... The code is the handle for every other command.

```
debates/
  D0001-is-remote-work-net-positive-for-early-stage/
    D0001.json               state (resumable)
    D0001-00-spec.toml       effective spec: re-run it with `syzetetes run`
    D0001-01-transcript.md   live log
    D0001-02-report.md       final referenced report
    D0001-03-chat.md         Q&A log, written by `syzetetes chat`
    D0001-04-review.html     interactive review, written at the end of a run and by `syzetetes review`
```

`resume`, `render`, `review`, `chat` and `rerun` accept the code (`D0001`, or just `d1`) or a folder path.

## Commands

```
syzetetes init [FILE]             write a commented spec template (default syzetetes.toml)
syzetetes run TOPIC|SPEC.toml     start a debate; flags override the spec
syzetetes resume CODE             continue an interrupted run from its last saved step
syzetetes rerun CODE [...]        replay a finished run from a chosen round with new input
syzetetes review CODE             write and open the interactive review
syzetetes chat CODE [QUESTION]    grounded Q&A over the report
syzetetes list                    runs, codes and status
syzetetes render CODE             re-render the report from saved state
syzetetes config                  print the effective defaults
```

`syzetetes run --help` lists every flag; each maps to a spec key. Ctrl-C at any time is safe.

## What it costs

Every model call is a `claude -p` or `codex exec` subprocess, so usage lands on your two subscriptions,
never on an API bill. A default run (Opus high, Codex high, Sonnet referee, up to 8 rounds, web research
on) is roughly 30 to 35 model calls, each carrying the growing transcript. Expect a noticeable dent in
both weekly quotas. The smoke-test recipe above costs almost nothing. `chat` calls are tiny.

## Configuration defaults

Three layers, each overriding the last: built-in defaults, `~/.config/syzetetes/config.toml` (same keys
as the `[models]` and `[debate]` sections, flat), then the spec file, then CLI flags.

```toml
# ~/.config/syzetetes/config.toml
claude_model = "opus"
codex_model = "gpt-6.1-sol"
referee = "claude"
max_rounds = 6
pause = "disputes"
out_dir = "~/debates"
```

## Design notes

- Each model call is single-shot with the full needed context in the prompt. There is no CLI session
  state, so a crash loses at most one call.
- Both CLIs run isolated from your personal settings: no MCP servers, plugins, hooks, CLAUDE.md or
  AGENTS.md. Codex runs read-only in a temp dir.
- Structured output is enforced by each CLI's JSON-schema mode and re-validated locally; a malformed
  answer is sent back with the validation errors and re-asked.
- The ledger is the source of truth. The report's verdict sections are rendered from it, not from free
  prose, and a referee that drops a claim has it restored automatically.
- The debaters are symmetric: the only difference between Claude's and Codex's prompts is who they are
  told they are.
- Human input is typed. Opinions and facts are stored separately, rendered separately in every prompt,
  and labelled in the report and the review, so a reader can always tell what the models concluded on
  their own.

## Layout

```
syzetetes/
  cli.py       commands
  spec.py      spec template, loading, effective spec
  engine.py    phases, ledger, termination, checkpoints, derive (rerun)
  agents.py    subprocess wrappers for the Claude Code and Codex CLIs
  prompts.py   every prompt
  schemas.py   JSON schemas and a small validator
  report.py    Markdown report with numbered references
  review.py    interactive HTML review
  chat.py      grounded Q&A over a finished report
  runs.py      run codes, folder layout, source loading
  config.py    defaults, user config file, overrides
examples/      runnable spec files for each recipe
tests/         scripted fake agents; no CLIs or network needed
```

## Tests

```
.venv/bin/pip install pytest && .venv/bin/python -m pytest -q
```

## Contributing

Issues and pull requests are welcome. Keep the debaters symmetric, keep the ledger as the single source
of truth, give every new flag a spec key, and add a fake-agent test for any change to the engine.

## License

[MIT](LICENSE).
