# Syzetetes

*Syzetetes* (Greek συζητητής, "one who investigates together") makes two different AI models research a
question, argue it out in structured rounds under a bookkeeping referee, and hand you a referenced report
of what they agreed on, what they still dispute, and why. You can seed it with your own context, sources,
opinions and facts; steer it while it runs; replay it with hindsight; review visually how every claim
moved; and afterwards ask questions that are answered only from what the debate produced.

- **Claude** debates through the [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI on your Claude subscription.
- **Codex** debates through the [Codex](https://github.com/openai/codex) CLI on your ChatGPT subscription.
- **Jev**, [TypeSafe AI](https://typesafe.ai)'s decision model, referees: it judges every claim after every
  round with a calibrated confidence and writes no text. Needs a `TYPESAFE_API_KEY` (cents per debate).
  You can referee with an LLM instead (`--referee claude`), with no key at all.
- Nothing else leaves your machine.
- Zero Python dependencies. Python 3.11+.

See [example-report.md](example-report.md) for a finished report and [examples/](examples/) for ready-made specs.

## Contents

- [Why two models and a decision model](#why-two-models-and-a-decision-model)
- [Install](#install)
- [Five-minute tour](#five-minute-tour)
- [How a run works](#how-a-run-works)
- [The spec file](#the-spec-file)
- [Recipes](#recipes)
  - [Cheapest possible run](#cheapest-possible-run)
  - [Give it your context and sources](#give-it-your-context-and-sources)
  - [Tell it what you think](#tell-it-what-you-think)
  - [Establish a fact it must not argue with](#establish-a-fact-it-must-not-argue-with)
  - [Decide when it stops and asks you](#decide-when-it-stops-and-asks-you)
  - [Replay a finished debate with hindsight](#replay-a-finished-debate-with-hindsight)
  - [How the Jev referee works](#how-the-jev-referee-works)
  - [Let an LLM referee instead](#let-an-llm-referee-instead)
  - [Review how the synthesis was reached](#review-how-the-synthesis-was-reached)
  - [Interrogate the result](#interrogate-the-result)
  - [Reproduce a run](#reproduce-a-run)
- [Run folders and codes](#run-folders-and-codes)
- [Commands](#commands)
- [What it costs](#what-it-costs)
- [Configuration defaults](#configuration-defaults)
- [Design notes](#design-notes)
- [Layout, tests, contributing, license](#layout)

## Why two models and a decision model

A single model asked to "consider both sides" tends to produce a tidy, agreeable survey. Two models with
different training, forced to answer each other's claims one by one with sources, produce something
closer to a real argument: concessions with reasons, disputes narrowed to their crux, and an honest list
of what nobody could settle.

The referee is deliberately not a third LLM. Jev is a decision model: given a claim and what each side
said about it this round, it returns a status, who moved, whether a side merely repeated itself, the kind
of crux, whose case is stronger, and whether you are needed, each as a probability. It cannot argue,
cannot write, and cannot favour the model that shares its training. A small LLM scribe writes the words
around those verdicts and cannot change them. The result is a ledger you can audit: every status has a
confidence, and the unsure ones can be handed to you.

## Install

As a command on your PATH (recommended):

```
pipx install git+https://github.com/narmirzaei/syzetetes      # or: uv tool install git+https://github.com/narmirzaei/syzetetes
syzetetes --help
```

For development, from a clone, so edits take effect immediately:

```
git clone https://github.com/narmirzaei/syzetetes && cd syzetetes
pipx install --editable .           # global command, editable
python3 -m venv .venv && .venv/bin/pip install -e . pytest    # venv for the tests
```

Requires `claude` and `codex` on your PATH, both logged in (`claude` and `codex login`), and a TypeSafe
key for the referee: put `TYPESAFE_API_KEY=...` in `./.env.local` or export it (get one at
https://console.typesafe.ai/keys). Without a key, pass `--referee claude` or `--referee codex`.

## Five-minute tour

```
syzetetes init -i              # asks you everything; creates debates/D0001-<name>/ with D0001-00-spec.toml
syzetetes run D0001            # research → openings → rounds → closings → synthesis → report
syzetetes review D0001         # interactive page: how every claim moved until the synthesis
syzetetes chat D0001           # ask questions, answered only from the report
syzetetes list                 # every run, its code and status
```

`init` allocates the run up front: a sequential code, a folder named after the question, and the spec
inside it. Without `-i` it writes the blank commented template for you to fill in by hand
(`syzetetes init "the question"` names the folder straight away). Nothing is sent to a model until `run`.

No spec needed for a quick one:

```
syzetetes run "Is remote work net positive for early-stage startups?"
```

## How a run works

1. **Research.** Both models independently search the web and write a cited briefing. Briefings are shared.
2. **Opening positions.** Each states a thesis and falsifiable claims with sources.
3. **Rounds.** Debaters alternate (who speaks first flips each round). Every turn must answer the other
   side's claims by ID with one stance each: accept, maintain (with a *new* argument), revise, or agree to
   disagree. After each round the **referee** judges every claim: Jev decides status, who moved, repetition,
   crux kind, whose case is stronger and whether you are needed, each with a confidence; a scribe LLM
   writes the crux, the round summary and a nudge to a side that is restating itself.
4. **Termination.** The debate ends when every claim is settled, when both sides say they have nothing new,
   when the ledger has not moved for `stable_rounds` rounds, or at the round cap.
5. **Human checkpoints.** The run stops and asks you in the situations you chose (by default: when the
   referee says a human decision is needed, or the ledger stalls). You can let it continue, stop it, give
   an opinion, or establish a fact.
6. **Closing and synthesis.** Each side writes a closing statement. The scribe LLM writes the executive
   summary, per-claim verdicts, the strongest case for and against, and guidance for you, with Jev's
   final verdict table in front of it.
7. **Report and review.** A Markdown report with every argument, the agreed / conceded / disputed /
   agree-to-disagree points, closing statements, briefings, the full transcript and a numbered reference
   list; and an interactive HTML review of how the ledger moved.

While it runs, the terminal shows a live status line (phase, round, who is thinking and for how long)
and a coloured ledger bar after every referee pass; the transcript file in the run folder is appended
live so you can read along. Redirect stderr to a file and the display degrades to plain log lines.

## The spec file

Everything a run needs lives in one TOML file, `<code>-00-spec.toml`, inside the run folder.
`syzetetes init` creates the folder and writes a commented template; `syzetetes init --interactive`
(`-i`) walks you through every setting with its default and writes the filled-in file, including the
replay section if you choose to derive from an earlier run. Every key is optional except `topic`, and
every CLI flag has a key here. A flag given on the command line overrides the
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
referee = "jev"              # jev (default) | claude | codex
judge_model = "jev-latest"   # jev-latest | jev-preview | jev-1.14.0
scribe = "claude"            # which CLI writes the prose under jev
referee_model = "haiku"      # the scribe's model under jev; the referee's model under claude/codex (then sonnet)
referee_effort = "low"

[debate]
max_rounds = 8
stable_rounds = 2            # stop after this many rounds with no status change
research = true
pause_on = ["referee", "stall"]   # when to stop and ask you; [] = never (see below)
out_dir = "debates"
timeout_s = 1800
retries = 3

# [rerun]                    # replay a finished run instead of starting fresh
# from = "D0001"
# keep_rounds = 2
# redo_openings = false
```

Paths in `context_files` and `sources` resolve relative to the spec file. `syzetetes run` also accepts a
spec file anywhere on disk (`syzetetes run examples/cheap-smoke-test.toml`), in which case a new code is
allocated. A run started from a topic saves the spec it ran with, so any run can be reproduced or copied.

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
pause_on = []
```

```
syzetetes run "Tabs or spaces for Python?" --claude-model haiku --claude-effort low --codex-effort low \
  --max-rounds 1 --no-research --unattended
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

### Decide when it stops and asks you

`pause_on` is a list of situations, checked after every round. Any that holds stops the run and asks you.
[examples/hands-on-moderation.toml](examples/hands-on-moderation.toml)

| situation | meaning |
|---|---|
| `"referee"` | the referee cannot resolve something on its own (conflicting sources, a value judgement, scope) |
| `"stall"` | nothing changed for `stable_rounds` rounds. Without this, a stall simply ends the debate |
| `"disputes"` | after every round that still has a disputed claim: you tie-break each one |
| `"agree_to_disagree"` | a side wants to agree to disagree on a claim: weigh in before it is dropped |
| `"low_confidence"` | with the Jev referee: the judge was unsure (below 0.60) about a claim's status |
| `"every_round"` | after every round |
| `"round:3"` | once, after round 3 |
| `"custom:EXPR"` | your own condition over `round`, `disputed`, `open`, `agreed`, `conceded`, `agree_to_disagree`, `total`, `unchanged` |

The default is `["referee", "stall"]`. An empty list never asks (`--unattended`); deadlocks become
agree-to-disagree. `syzetetes init -i` presents the same list as a multiple-choice question.

```toml
[debate]
pause_on = ["referee", "stall", "disputes"]                 # moderate every disagreement
pause_on = ["referee", "agree_to_disagree", "round:3"]      # only when it gets interesting
pause_on = ["referee", "custom:disputed >= 2 and round >= 2"]
```

```
syzetetes run "Is remote work net positive for early-stage startups?" --pause-on referee,stall,disputes
```

At a checkpoint you see the open disputes and type one of:

```
continue                 carry on
stop                     end the debate now; closings and synthesis still run
extend 2                 at the round cap: allow two more rounds
opinion: <your view>     recorded as your opinion; the debate continues with it
fact: <statement>        recorded as a binding fact; the debate continues with it
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
pause_on = ["referee", "stall", "disputes"]   # and moderate the replay yourself
```

```
syzetetes rerun D0001 --keep-rounds 2 --fact "Korea's 2024 TFR was 0.75." --pause-on referee,stall,disputes
syzetetes rerun D0001 --opinion "..."                     # inject after the openings, replay all rounds
syzetetes rerun D0001 --redo-openings --opinion "..."     # inject before the openings; keep only research
syzetetes rerun D0001 --source https://new-paper.org      # new sources: research is redone too
syzetetes rerun D0001 --keep-rounds 3 --claude-model fable --max-rounds 10   # change models or shape
```

### How the Jev referee works

The default. [Jev](https://typesafe.ai) (TypeSafe AI's decision model) judges **every claim after every
round** with calibrated probabilities, and a small LLM scribe only writes the words around those
verdicts; it cannot change them. [examples/jev-referees.toml](examples/jev-referees.toml)

```toml
[models]
referee = "jev"
judge_model = "jev-latest"    # or jev-preview, jev-1.14.0
scribe = "claude"             # which CLI writes the prose and the synthesis
referee_model = "haiku"       # the scribe's model; haiku is plenty
[debate]
pause_on = ["referee", "stall", "low_confidence"]   # also stop when Jev is unsure about a status
```

```
syzetetes run "..."                                      # Jev referees by default
syzetetes rerun D0001 --keep-rounds 0                    # re-judge an older LLM-refereed debate from the openings
```

What Jev decides, per claim, per round, each with a confidence: status (agreed / conceded / disputed /
agree to disagree / open), who moved, whether each side merely repeated itself, whether an evidence
request was answered, the kind of crux (factual, value judgement, scope, missing evidence), whose case
is currently stronger, and whether a human decision is needed. New claims are checked for duplicates
against every existing claim. Claims are numbered by code, so none can be dropped or renumbered.
`settled`, stalls and thresholds are computed in code, never asked.

What the scribe writes: both sides' positions, the crux wording, the round summary, nudges for a side
Jev flagged, the question for you when Jev says a human is needed, and the final synthesis (which is
given Jev's verdict table).

What you get that the LLM referee cannot give: a confidence on every status (faded cells and a dashed
outline for unsure ones in the review page), a "whose case is stronger" lean per claim, the full
probability split in the review page, a `low_confidence` pause trigger, and an audit line per claim in
the transcript (`K7: disputed→agreed (0.91), moved codex, lean codex (0.64)`).

Cost and caveats. This is the one place Syzetetes uses an API key: Jev bills $0.042 per million input
tokens, output is free, and a 16-claim, 4-round debate is a few hundred thousand tokens, a cent or two;
the run prints the exact token count at the end. Jev's benchmarks are vendor-run. Its documented
weaknesses are handled (each claim gets a small state about this round only; every choice is asked twice
with the options reversed and averaged to cancel first-option bias; nothing is counted or computed by
the model), but measure it on your own debates: run the same spec with `--referee claude` and compare
the two reports.

### Let an LLM referee instead

No TypeSafe key, or you want to compare: an LLM rewrites the whole ledger after each round. It gives no
confidences and it is a frontier model judging frontier models, so pick the other provider's model if that
worries you. [examples/codex-referees.toml](examples/codex-referees.toml)

```toml
[models]
referee = "codex"              # or "claude"
referee_model = "gpt-6.1-sol"  # defaults to sonnet / medium for claude
```

```
syzetetes run "..." --referee claude
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
syzetetes init [TOPIC] [-i]       create a run folder (code + name) with its spec; -i fills it in
syzetetes run CODE|SPEC|TOPIC     start a debate from an init'd code, a spec file, or a question
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

Debater, scribe and chat calls are `claude -p` or `codex exec` subprocesses, so they land on your two
subscriptions. A default run (Opus high, Codex high, up to 8 rounds, web research on) is roughly 30 to 35
such calls, each carrying the growing transcript; expect a noticeable dent in both weekly quotas. The
referee's Jev calls are billed to your TypeSafe key at $0.042 per million input tokens: a cent or two per
debate, printed at the end of each run. The smoke-test recipe above costs almost nothing.

## Configuration defaults

Three layers, each overriding the last: built-in defaults, `~/.config/syzetetes/config.toml` (same keys
as the `[models]` and `[debate]` sections, flat), then the spec file, then CLI flags.

```toml
# ~/.config/syzetetes/config.toml
claude_model = "opus"
codex_model = "gpt-6.1-sol"
referee = "jev"
max_rounds = 6
pause_on = ["referee", "stall", "disputes"]
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
  judge.py     Jev client and the per-claim decision questions
  agents.py    subprocess wrappers for the Claude Code and Codex CLIs
  prompts.py   every prompt
  schemas.py   JSON schemas and a small validator
  report.py    Markdown report with numbered references
  review.py    interactive HTML review
  ui.py        terminal status line and ledger bar
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
