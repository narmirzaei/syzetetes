<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-wordmark-dark.svg">
    <img src="assets/logo-wordmark.svg" alt="Syzetetes" width="236">
  </picture>
</p>

*Syzetetes* (Greek συζητητής, "one who investigates together") makes two different AI models research a
question, argue it out in structured rounds under a bookkeeping referee, and hand you a referenced report
of what they agreed on, what they still dispute, and why. You can seed it with your own context, sources,
opinions and facts; steer it while it runs; replay it with hindsight; review visually how every claim
moved; and afterwards ask questions that are answered only from what the debate produced.

- **Claude** debates through the [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI on your Claude subscription.
- **Codex** debates through the [Codex](https://github.com/openai/codex) CLI on your ChatGPT subscription.
- One of them **referees**: keeps the claim ledger and writes the synthesis.
- **Jev**, [TypeSafe AI](https://typesafe.ai)'s decision model, **judges**: after every round it rules
  independently on every claim with a calibrated confidence, and its disagreements go back into the debate.
  Needs a `TYPESAFE_API_KEY` (cents per debate); without one the judge is skipped and nothing else changes.
- Nothing else leaves your machine.
- Zero Python dependencies. Python 3.11+.

See [example-report.md](example-report.md) for a finished report (a cheap one-round smoke debate, with the
judge's rulings and the referee's verdict) and [examples/](examples/) for ready-made specs.

## The players

| player | who | role |
|---|---|---|
| **Debater: Claude** | Claude, through the Claude Code CLI on your subscription | Researches the question, states falsifiable claims with sources, and answers Codex's claims one by one every round: accept, maintain with a new argument, revise, or agree to disagree. |
| **Debater: Codex** | Codex (OpenAI), through the Codex CLI on your ChatGPT subscription | The same, from different training. The two debaters get identical prompts; only the name differs. |
| **Referee** | An LLM, Claude by default (Sonnet), or Codex | Never argues. Keeps the claim ledger: assigns IDs, sets each claim's status from what was actually said, names the crux of each dispute, flags repetition, asks for your decision when the debaters cannot progress. Writes the closing synthesis and the verdict. |
| **Judge** | Jev, TypeSafe AI's decision model (optional, needs an API key) | Never writes a word. After every round, rules independently on every claim with a calibrated confidence: status, who moved, repetition, kind of crux, whose case is stronger, whether you are needed. Where it confidently disagrees with the referee, the debaters and the referee must answer it next round. |
| **You** | The human | Set the question and the starting point; optionally seed opinions (not binding) and facts (binding); decide when the run pauses for you; rule at pauses; replay with hindsight; interrogate the result afterwards. |

## Contents

- [The players](#the-players)
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
  - [How the judge works](#how-the-judge-works)
  - [Let Codex referee, or run without a judge](#let-codex-referee-or-run-without-a-judge)
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

Even so, LLM debates drift toward consensus: a debater accepts a reworded claim to move on, and an LLM
referee records it as agreement. The judge exists to resist that. Jev is a decision model: given a claim
and what each side said about it this round, it returns a status, who moved, whether a side merely
repeated itself, the kind of crux, whose case is stronger, and whether you are needed, each as a
probability. It cannot argue, cannot write, and cannot be polite. Where it confidently disagrees with the
referee, both debaters must say whether they really accept the claim, and the referee must either adopt
the judge's status or justify its own. Every claim is ruled on twice, and the debate has to resolve the
difference. Every status in the report carries a confidence, and the contested ones are marked.

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

Requires `claude` and `codex` on your PATH, both logged in (`claude` and `codex login`). For the judge,
put `TYPESAFE_API_KEY=...` in `./.env.local` or export it (get one at https://console.typesafe.ai/keys).
Without a key the run prints one warning and proceeds without the judge.

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
   disagree. After each round the **referee** (an LLM; bookkeeping only, never argues) updates the claim
   ledger, flags repetition, and nudges a side that is restating itself. Then the **judge** (Jev) rules
   on every claim in that ledger with a confidence. Confident disagreements, and a clear lean toward one
   side's case, become questions both debaters and the referee must answer in the next round.
4. **Termination.** The debate ends when every claim is settled, when both sides say they have nothing new,
   when the ledger has not moved for `stable_rounds` rounds, or at the round cap.
5. **Human checkpoints.** The run stops and asks you in the situations you chose (by default: when the
   referee cannot resolve something, or the ledger stalls; optionally when the judge overrules the
   referee). You can let it continue, stop it, give an opinion, or establish a fact.
6. **Closing and synthesis.** Each side writes a closing statement. The referee then writes its
   verdict, the result of the debate in plain words, plus the executive summary, per-claim verdicts, the
   strongest case for and against, and guidance for you, with the judge's final rulings in front of it.
7. **Report and review.** A Markdown report with the executive summary, the agreed / conceded / disputed /
   agree-to-disagree points, both closing statements followed by the referee's verdict, briefings, the full
   transcript and a numbered reference list; and an interactive HTML review of how the ledger moved. The
   verdict is also printed in the terminal when the run ends.

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
sources = ["https://example.org/paper", "papers/jones-2022.txt"]     # both sides must read, cite, check
opinions = ["I suspect pensions are the real issue, not fertility."]   # not binding; they must engage with it
facts = ["Scope is economics only; ignore climate arguments."]         # binding; treated as true

[models]
claude_model = "opus"        # opus | sonnet | haiku | fable | full model id
claude_effort = "high"       # low | medium | high | xhigh | max
codex_model = "gpt-6.1-sol"  # whatever your ChatGPT plan allows; defaults to ~/.codex/config.toml
codex_effort = "high"
referee = "claude"           # claude | codex: keeps the ledger, writes the synthesis
referee_model = "sonnet"
referee_effort = "medium"
judge = "jev"                # jev | none: rules on every claim after every round
judge_model = "jev-latest"   # jev-latest | jev-preview | jev-1.14.0

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

Paths in `context_files` and `sources` resolve relative to the spec file and must stay inside its folder: a spec is data that may come from someone else, so it cannot read your other files into a prompt. Files elsewhere go through `--context` and `--source`, which are yours. `syzetetes run` also accepts a
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
context_files = ["my-notes.md"]                   # relative to the spec file; its text goes to both sides
sources = [
  "https://tom.preston-werner.com/2010/08/23/readme-driven-development.html",
  "https://www.pragmaticengineer.com/working-backwards",
]
```

```
syzetetes run "Should a solo founder ..." --note "I am a solo technical founder ..." \
  --context examples/my-notes.md --source https://tom.preston-werner.com/2010/08/23/readme-driven-development.html
```

A `--source` can also be a local file, whose text is embedded (up to 40k characters).

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
| `"judge_disagrees"` | the judge confidently (0.70+) overrules the referee on a claim's status |
| `"low_confidence"` | the judge was unsure (below 0.60) about a claim's status |
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

### How the judge works

The default. After the referee writes each round's ledger, [Jev](https://typesafe.ai) (TypeSafe AI's
decision model) rules on **every claim** independently: status, who moved, whether each side merely
repeated itself, whether an evidence request was answered, the kind of crux (factual, value judgement,
scope, missing evidence), whose case is currently stronger, and whether a human decision is needed, each
with a calibrated confidence. [examples/judge.toml](examples/judge.toml)

```toml
[models]
referee = "claude"
judge = "jev"
judge_model = "jev-latest"    # or jev-preview, jev-1.14.0
[debate]
pause_on = ["referee", "stall", "judge_disagrees"]   # also stop when the judge confidently overrules a status
```

What happens with the rulings:

- **Agreement** attaches the confidence to the referee's status. In the report: *Judge agrees: agreed with
  confidence 0.94*.
- **Disagreement** marks the claim contested. The report shows both rulings; the review page marks the
  cell with `!`; the transcript records it.
- **Confident disagreement** (0.70 or above), and a confident lean toward one side on a disputed claim, is
  **fed back into the next round**: both debaters get the same list of questions ("the referee recorded
  K3 as agreed; the judge rules disputed (0.81). Say plainly whether you accept this claim as worded, and
  why"), and the referee must either adopt the judge's status or keep its own and say why in the crux.
  The rulings are explicitly not binding on the debaters; they must answer with evidence, not deference.
- `low_confidence` and `judge_disagrees` pause situations let you rule on exactly the claims in question.
- The synthesis receives the judge's final rulings as a table.

Why it is worth it: in a four-round Opus-versus-Codex debate on population decline
([examples/population-collapse.toml](examples/population-collapse.toml)), the Sonnet referee
ended with 15 of 16 claims "agreed"; Jev rated five of the late agreements between 0.2 and 0.55 and read
them as conceded or still disputed. Those are the claims a writer most needs re-examined, and nothing
else in the loop surfaces them.

Cost and caveats. This is the one place Syzetetes uses an API key: Jev bills $0.042 per million input
tokens, output is free, and a full four-round debate costs about a cent; the run prints the exact token
count at the end. Jev's benchmarks are vendor-run. Its documented weaknesses are handled (each claim gets
a small state about this round only; every choice is asked twice with the options reversed and averaged
to cancel first-option bias; nothing is counted or computed by the model), and it only sees what the
debaters tagged by claim ID, which is why the LLM referee, which reads everything, keeps the ledger.

### Let Codex referee, or run without a judge

[examples/codex-referees.toml](examples/codex-referees.toml)

```toml
[models]
referee = "codex"              # Codex keeps the ledger; the judge still rules
referee_model = "gpt-6.1-sol"
judge = "none"                 # no TypeSafe key, or a plain run: no confidences, no contested claims
```

```
syzetetes run "..." --referee codex --referee-model gpt-6.1-sol
syzetetes run "..." --judge none
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

Debater, referee and chat calls are `claude -p` or `codex exec` subprocesses, so they land on your two
subscriptions. A default run (Opus high, Codex high, Sonnet referee, up to 8 rounds, web research on) is
roughly 30 to 35 such calls, each carrying the growing transcript; expect a noticeable dent in both weekly
quotas. The judge's Jev calls are billed to your TypeSafe key at $0.042 per million input tokens: about
a cent per debate, printed at the end of each run. The smoke-test recipe above costs almost nothing.

## Configuration defaults

Three layers, each overriding the last: built-in defaults, `~/.config/syzetetes/config.toml` (same keys
as the `[models]` and `[debate]` sections, flat), then the spec file, then CLI flags.

```toml
# ~/.config/syzetetes/config.toml
claude_model = "opus"
codex_model = "gpt-6.1-sol"
referee = "claude"
judge = "jev"
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
  judge.py     Jev client and the per-claim rulings
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

Issues and pull requests are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md) for the engineering rules
and the contributor license grant. In short: keep the debaters symmetric, keep the ledger as the single
source of truth, give every new flag a spec key, add a fake-agent test for any change to the engine, and
update the README recipes, `examples/` and `example-report.md` in the same commit as the feature.

## License

Source-available. Free to use, study, change and share for personal, research, educational, hobby and
nonprofit purposes under the [PolyForm Noncommercial 1.0.0](LICENSE) license. **Commercial use of any
kind requires a separate license** from the author: open an issue to ask.

Relicensed from MIT on 2026-10-21. The snapshot published under MIT before that date remains available
under MIT to anyone who obtained it then.
