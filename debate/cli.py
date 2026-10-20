"""debate — have Claude and Codex research a topic, debate it, and write a referenced report."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .config import USER_CONFIG, Config, load_config
from .engine import Debate
from .runs import list_runs, resolve


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="debate", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="start a new debate")
    run.add_argument("topic", help="the question or proposition to debate")
    run.add_argument("--context", action="append", default=[], metavar="FILE",
                     help="file with extra context for both sides (repeatable); use '-' for stdin")
    run.add_argument("--note", default="", help="short extra context given inline")
    _human_opts(run)
    _model_opts(run)

    rr = sub.add_parser("rerun", help="re-run a finished debate from a chosen round with your opinion or ruling added")
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

    ls = sub.add_parser("list", help="list runs and their codes")
    ls.add_argument("--out", dest="out_dir", help="directory holding run folders (default: ./debates)")

    sub.add_parser("config", help="print the effective configuration")
    return p


def _human_opts(p: argparse.ArgumentParser):
    h = p.add_argument_group("your input")
    h.add_argument("--opinion", action="append", default=[], metavar="TEXT",
                   help="your view, not binding: the debaters must engage with it (repeatable)")
    h.add_argument("--ruling", action="append", default=[], metavar="TEXT",
                   help="a binding ruling / veto both debaters treat as settled (repeatable)")


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
    g.add_argument("--referee", choices=["claude", "codex"], help="which CLI runs the bookkeeping referee")
    g.add_argument("--referee-model")
    g.add_argument("--referee-effort")
    d = p.add_argument_group("debate")
    d.add_argument("--max-rounds", type=int)
    d.add_argument("--stable-rounds", type=int, help="stop after this many rounds with no ledger change")
    d.add_argument("--no-research", dest="research", action="store_false", default=None)
    d.add_argument("--pause", choices=["never", "referee", "disputes", "always"],
                   help="when to stop and ask you: never | referee (default: referee asks or stall) | "
                        "disputes (every round with a disputed claim) | always (every round)")
    d.add_argument("--pause-when", metavar="EXPR",
                   help='also pause when EXPR is true, over round, disputed, open, agreed, conceded, '
                        'agree_to_disagree, total, unchanged; e.g. "disputed >= 2 and round >= 2"')
    d.add_argument("--unattended", action="store_true", default=None, help="same as --pause never")
    d.add_argument("--out", dest="out_dir", help="directory for run folders (default: ./debates)")
    d.add_argument("--timeout", dest="timeout_s", type=int, help="seconds per model call")


log = logging.getLogger("debate")


def main(argv: list[str] | None = None) -> int:
    try:
        return _main(argv)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


def _main(argv: list[str] | None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        datefmt="%H:%M:%S", stream=sys.stderr)
    if args.cmd == "config":
        cfg = load_config()
        print(f"# effective config (user file: {USER_CONFIG}{'' if USER_CONFIG.exists() else ' — not present'})")
        for k, v in cfg.to_dict().items():
            print(f"{k} = {json.dumps(v)}")
        return 0

    if args.cmd in ("render", "resume", "chat", "list", "rerun"):
        out_dir = Path(args.out_dir or load_config().out_dir)

    if args.cmd == "list":
        for f in list_runs(out_dir):
            state = json.loads(f.state.read_text()) if f.state.exists() else {}
            status = "done" if f.report.exists() else state.get("phase", "?")
            print(f"{f.code}  {status:<10} {state.get('topic', f.dir.name)}")
        return 0

    if args.cmd == "render":
        files = resolve(args.run, out_dir)
        state = json.loads(files.state.read_text())
        d = Debate(files, Config().apply_overrides(state["config"]), agents={})
        d.state = state
        print(d._write_report())
        return 0

    if args.cmd == "chat":
        from .chat import one_shot, repl
        files = resolve(args.run, out_dir)
        return one_shot(files, args.question) if args.question else repl(files)

    if args.cmd == "rerun":
        overrides = {k: v for k, v in vars(args).items()
                     if k not in ("cmd", "run", "keep_rounds", "redo_openings", "opinion", "ruling") and v is not None}
        d = Debate.derive(resolve(args.run, out_dir).dir, overrides, keep_rounds=args.keep_rounds,
                          redo_openings=args.redo_openings, rulings=args.ruling, opinions=args.opinion)
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

    overrides = {k: v for k, v in vars(args).items()
                 if k not in ("cmd", "topic", "context", "note", "opinion", "ruling") and v is not None}
    cfg = load_config(overrides)
    context_parts = [args.note] if args.note else []
    for f in args.context:
        context_parts.append(sys.stdin.read() if f == "-" else Path(f).read_text())
    context = "\n\n".join(p.strip() for p in context_parts if p.strip())

    d = Debate.create(args.topic, context, cfg, rulings=args.ruling, opinions=args.opinion)
    log.info("run %s: %s", d.code, d.dir)
    return _drive(d)


def _drive(d: Debate) -> int:
    log.info("Claude: %s | Codex: %s | Referee: %s | pause: %s%s",
             d.agents["claude"].label, d.agents["codex"].label, d.agents["referee"].label,
             d.cfg.pause, f" or when {d.cfg.pause_when!r}" if d.cfg.pause_when else "")
    try:
        report = d.run()
    except KeyboardInterrupt:
        print(f"\nInterrupted. Resume with: debate resume {d.code}", file=sys.stderr)
        return 130
    print(f"\nReport: {report}\nAsk about it: debate chat {d.code}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
