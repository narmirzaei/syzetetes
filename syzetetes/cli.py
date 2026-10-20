"""Syzetetes — Claude and Codex research a topic, debate it, and write a referenced report."""
from __future__ import annotations

import argparse
import json
import logging
import tomllib
import re
import sys
from pathlib import Path

from .config import USER_CONFIG, Config, load_config
from .engine import Debate
from .runs import RunFiles, list_runs, load_sources, load_state, new_run, resolve
from .spec import DEFAULT_NAME, config_overrides, inputs, load_spec, template, wizard
from .ui import progress, setup_logging


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="syzetetes", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    init = sub.add_parser("init", help="create a new run folder (code + name) with its spec file, ready to run")
    init.add_argument("topic", nargs="?", default="", help="the question; names the folder (optional with -i)")
    init.add_argument("-i", "--interactive", action="store_true",
                      help="ask for every setting and write a filled-in spec instead of a blank template")
    init.add_argument("--out", dest="out_dir", help="directory holding run folders (default: ./debates)")

    run = sub.add_parser("run", help="start a debate: from a run code made by `init`, a spec file, or a topic")
    run.add_argument("topic", help="a run code (D0002, from `syzetetes init`), a .toml spec file, or the question itself")
    run.add_argument("--context", action="append", default=[], metavar="FILE",
                     help="file with extra context for both sides (repeatable); use '-' for stdin")
    run.add_argument("--note", default="", help="short extra context given inline")
    _human_opts(run)
    _model_opts(run)

    rr = sub.add_parser("rerun", help="re-run a finished debate from a chosen round with your opinion or fact added")
    rr.add_argument("run", help="run code (D0001) or path to the run folder")
    rr.add_argument("--keep-rounds", type=int, default=0, metavar="N",
                    help="inherit rounds 0..N (0 = keep only the opening positions; default 0)")
    rr.add_argument("--redo-openings", action="store_true", help="inherit only the research; redo openings too")
    _human_opts(rr)
    _model_opts(rr)

    res = sub.add_parser("resume", help="resume an interrupted debate")
    _run_ref(res)
    res.add_argument("--unattended", action="store_true", default=None)

    ren = sub.add_parser("render", help="re-render a run's report from its saved state")
    _run_ref(ren)

    ch = sub.add_parser("chat", help="ask questions about a finished debate, answered only from its report")
    _run_ref(ch)
    ch.add_argument("question", nargs="?", help="ask one question and exit (default: interactive)")

    rv = sub.add_parser("review", help="write (and open) the interactive HTML review of how the synthesis was reached")
    _run_ref(rv)
    rv.add_argument("--no-open", action="store_true", help="only write the file; do not open it in the browser")

    ls = sub.add_parser("list", help="list runs and their codes")
    ls.add_argument("--out", dest="out_dir", help="directory holding run folders (default: ./debates)")

    sub.add_parser("config", help="print the effective configuration")
    return p


def _human_opts(p: argparse.ArgumentParser):
    h = p.add_argument_group("your input")
    h.add_argument("--opinion", action="append", default=[], metavar="TEXT",
                   help="your view, not binding: the debaters must engage with it (repeatable)")
    h.add_argument("--fact", action="append", default=[], metavar="TEXT",
                   help="binding: both debaters treat it as true for this debate (repeatable)")
    h.add_argument("--source", action="append", default=[], metavar="URL|FILE",
                   help="a source both sides must start from and cite (repeatable); on rerun, redoes research")


def _run_ref(p: argparse.ArgumentParser):
    p.add_argument("run", help="run code (D0001) or path to the run folder")
    p.add_argument("--out", dest="out_dir", help="directory holding run folders (default: ./debates)")
    return p


def _model_opts(p: argparse.ArgumentParser):
    g = p.add_argument_group("models")
    g.add_argument("--claude-model", help="opus | sonnet | haiku | fable | full model id")
    g.add_argument("--claude-effort", help="low | medium | high | xhigh | max")
    g.add_argument("--codex-model", help="any model your ChatGPT plan allows (default: your Codex config)")
    g.add_argument("--codex-effort", help="low | medium | high | xhigh | ultra")
    g.add_argument("--referee", choices=["claude", "codex", "jev"],
                   help="claude | codex: an LLM keeps the ledger; jev: TypeSafe's decision model judges every claim "
                        "(needs $TYPESAFE_API_KEY) and the LLM only writes prose")
    g.add_argument("--referee-model", help="referee model, or the scribe's model when --referee jev")
    g.add_argument("--referee-effort")
    g.add_argument("--scribe", choices=["claude", "codex"], help="with --referee jev: which CLI writes the prose")
    g.add_argument("--judge-model", help="with --referee jev: jev-latest | jev-preview | jev-1.14.0")
    d = p.add_argument_group("debate")
    d.add_argument("--max-rounds", type=int)
    d.add_argument("--stable-rounds", type=int, help="stop after this many rounds with no ledger change")
    d.add_argument("--no-research", dest="research", action="store_false", default=None)
    d.add_argument("--pause-on", metavar="LIST",
                   help="comma-separated situations in which to stop and ask you: referee, stall, every_round, "
                        "disputes, agree_to_disagree, round:N, custom:EXPR (default: referee,stall; empty = never)")
    d.add_argument("--unattended", action="store_true", default=None, help="never ask; same as --pause-on ''")
    d.add_argument("--out", dest="out_dir", help="directory for run folders (default: ./debates)")
    d.add_argument("--timeout", dest="timeout_s", type=int, help="seconds per model call")


log = logging.getLogger("syzetetes")


def main(argv: list[str] | None = None) -> int:
    try:
        return _main(argv)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


def _main(argv: list[str] | None) -> int:
    args = _parser().parse_args(argv)
    setup_logging()
    if args.cmd == "init":
        out_dir = Path(args.out_dir or load_config().out_dir)
        values = None
        if args.interactive:
            try:
                values = wizard()
            except (EOFError, KeyboardInterrupt):
                print("\naborted; nothing created", file=sys.stderr)
                return 130
            if args.topic and not values.get("topic") and not values.get("rerun"):
                values["topic"] = args.topic
        topic = (values or {}).get("topic") or args.topic
        name = topic or ((values or {}).get("rerun") or {}).get("from", "") and f"replay of {values['rerun']['from']}" or "untitled"
        files = new_run(out_dir, name)
        files.spec.write_text(template({**(values or {}), "topic": topic} if values or topic else None))
        print(f"Created {files.code}: {files.dir}/\n  {files.spec.name}  "
              + ("review it" if values else "fill in 'topic' and anything else")
              + f", then:  syzetetes run {files.code}")
        return 0

    if args.cmd == "config":
        cfg = load_config()
        print(f"# effective config (user file: {USER_CONFIG}{'' if USER_CONFIG.exists() else ' — not present'})")
        for k, v in cfg.to_dict().items():
            print(f"{k} = {json.dumps(v)}")
        return 0

    if args.cmd in ("render", "resume", "chat", "list", "rerun", "review"):
        out_dir = Path(args.out_dir or load_config().out_dir)

    if args.cmd == "list":
        for f in list_runs(out_dir):
            if f.state.exists():
                state = load_state(f)
                status, topic = ("done" if f.report.exists() else state.get("phase", "?")), state["topic"]
            elif f.spec.exists():
                spec = tomllib.loads(f.spec.read_text())
                topic = spec.get("topic") or (f"replay of {spec['rerun']['from']}" if spec.get("rerun") else "")
                status = "ready" if topic else "needs topic"
            else:
                status, topic = "?", ""
            print(f"{f.code}  {status:<12} {topic or f.dir.name}")
        return 0

    if args.cmd == "render":
        files = resolve(args.run, out_dir)
        state = load_state(files)
        d = Debate(files, Config().apply_overrides(state["config"]), agents={})
        d.state = state
        print(d._write_report())
        return 0

    if args.cmd == "review":
        from .review import write_review
        files = resolve(args.run, out_dir)
        out = write_review(files, load_state(files))
        print(out)
        if not args.no_open:
            import webbrowser
            webbrowser.open(out.resolve().as_uri())
        return 0

    if args.cmd == "chat":
        from .chat import one_shot, repl
        files = resolve(args.run, out_dir)
        return one_shot(files, args.question) if args.question else repl(files)

    if args.cmd == "rerun":
        overrides = {k: v for k, v in vars(args).items()
                     if k not in ("cmd", "run", "keep_rounds", "redo_openings", "opinion", "fact", "source")
                     and v is not None}
        d = Debate.derive(resolve(args.run, out_dir).dir, overrides, keep_rounds=args.keep_rounds,
                          redo_openings=args.redo_openings, facts=args.fact, opinions=args.opinion,
                          sources=load_sources(args.source))
        log.info("run %s derived from %s: %s", d.code, args.run, d.dir)
        return _drive(d)

    if args.cmd == "resume":
        d = Debate.resume(resolve(args.run, out_dir).dir)
        if args.unattended:
            d.cfg.unattended = True
            from .engine import unattended_checkpoint
            d.checkpoint = unattended_checkpoint
        report = d.run()
        print(f"\nReport: {report}")
        return 0

    flag_overrides = {k: v for k, v in vars(args).items()
                      if k not in ("cmd", "topic", "context", "note", "opinion", "fact", "source") and v is not None}
    spec_path, files = Path(args.topic), None
    if re.fullmatch(r"[dD]\d+", args.topic.strip()):
        files = resolve(args.topic, Path(load_config(flag_overrides).out_dir))
        if files.state.exists():
            print(f"error: {files.code} has already run; use `syzetetes resume {files.code}` or "
                  f"`syzetetes rerun {files.code}`", file=sys.stderr)
            return 2
        if not files.spec.exists():
            print(f"error: {files.code} has no spec file ({files.spec.name})", file=sys.stderr)
            return 2
        spec_path = files.spec
    if spec_path.suffix == ".toml" and spec_path.is_file():
        spec = load_spec(spec_path)
        inp = inputs(spec, spec_path.parent)
        overrides = {**config_overrides(spec), **flag_overrides}          # flags beat the file
        topic = inp["topic"]
        context_parts = [inp["context"], args.note]
        sources = inp["sources"] + args.source
        opinions = inp["opinions"] + args.opinion
        facts = inp["facts"] + args.fact
        rr = spec.get("rerun")
    else:
        overrides, topic, context_parts = flag_overrides, args.topic, [args.note]
        sources, opinions, facts, rr = args.source, args.opinion, args.fact, None
    for f in args.context:
        context_parts.append(sys.stdin.read() if f == "-" else Path(f).read_text())
    context = "\n\n".join(p.strip() for p in context_parts if p and p.strip())

    if rr:
        cfg_probe = load_config(overrides)
        d = Debate.derive(resolve(str(rr["from"]), Path(cfg_probe.out_dir)).dir, overrides,
                          keep_rounds=int(rr.get("keep_rounds", 0)), redo_openings=bool(rr.get("redo_openings", False)),
                          facts=facts, opinions=opinions, sources=load_sources(sources), files=files)
        log.info("run %s derived from %s: %s", d.code, rr["from"], d.dir)
        return _drive(d)
    cfg = load_config(overrides)
    d = Debate.create(topic, context, cfg, facts=facts, opinions=opinions, sources=load_sources(sources), files=files)
    log.info("run %s: %s", d.code, d.dir)
    return _drive(d)


def _drive(d: Debate) -> int:
    ref = f"{d.judge.label} judging, {d.agents['referee'].label} as scribe" if d.judge else d.agents["referee"].label
    log.info("Claude: %s | Codex: %s | Referee: %s | pause on: %s",
             d.agents["claude"].label, d.agents["codex"].label, ref, ", ".join(d.cfg.pause_on) or "nothing (unattended)")
    progress.start()
    try:
        report = d.run()
    except KeyboardInterrupt:
        progress.stop()
        print(f"\nInterrupted. Resume with: syzetetes resume {d.code}", file=sys.stderr)
        return 130
    finally:
        progress.stop()
    if d.judge is not None and getattr(d.judge, "calls", 0):
        print(f"\nJev: {d.judge.calls} calls, {d.judge.input_tokens:,} input tokens "
              f"(≈ ${d.judge.input_tokens / 1e6 * 0.042:.3f})")
    print(f"\nReport: {report}\nReview how it got there: syzetetes review {d.code}\nAsk about it: syzetetes chat {d.code}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
