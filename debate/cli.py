"""debate — have Claude and Codex research a topic, debate it, and write a referenced report."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .config import USER_CONFIG, Config, load_config
from .engine import Debate


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="debate", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="start a new debate")
    run.add_argument("topic", help="the question or proposition to debate")
    run.add_argument("--context", action="append", default=[], metavar="FILE",
                     help="file with extra context for both sides (repeatable); use '-' for stdin")
    run.add_argument("--note", default="", help="short extra context given inline")
    _model_opts(run)

    res = sub.add_parser("resume", help="resume an interrupted debate from its run directory")
    res.add_argument("run_dir")
    res.add_argument("--unattended", action="store_true", default=None)

    ren = sub.add_parser("render", help="re-render report.md from a run's saved state")
    ren.add_argument("run_dir")

    sub.add_parser("config", help="print the effective configuration")
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
    d.add_argument("--unattended", action="store_true", default=None,
                   help="never pause for a human; stalls end the debate")
    d.add_argument("--out", dest="out_dir", help="directory for run folders (default: ./debates)")
    d.add_argument("--timeout", dest="timeout_s", type=int, help="seconds per model call")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        datefmt="%H:%M:%S", stream=sys.stderr)
    log = logging.getLogger("debate")

    if args.cmd == "config":
        cfg = load_config()
        print(f"# effective config (user file: {USER_CONFIG}{'' if USER_CONFIG.exists() else ' — not present'})")
        for k, v in cfg.to_dict().items():
            print(f"{k} = {json.dumps(v)}")
        return 0

    if args.cmd == "render":
        run_dir = Path(args.run_dir)
        state = json.loads((run_dir / "state.json").read_text())
        d = Debate(run_dir, Config().apply_overrides(state["config"]), agents={})
        d.state = state
        print(d._write_report())
        return 0

    if args.cmd == "resume":
        d = Debate.resume(Path(args.run_dir))
        if args.unattended:
            d.cfg.unattended = True
            from .engine import unattended_checkpoint
            d.checkpoint = unattended_checkpoint
        report = d.run()
        print(f"\nReport: {report}")
        return 0

    overrides = {k: v for k, v in vars(args).items()
                 if k not in ("cmd", "topic", "context", "note") and v is not None}
    cfg = load_config(overrides)
    context_parts = [args.note] if args.note else []
    for f in args.context:
        context_parts.append(sys.stdin.read() if f == "-" else Path(f).read_text())
    context = "\n\n".join(p.strip() for p in context_parts if p.strip())

    d = Debate.create(args.topic, context, cfg)
    log.info("run directory: %s", d.dir)
    log.info("Claude: %s | Codex: %s | Referee: %s",
             d.agents["claude"].label, d.agents["codex"].label, d.agents["referee"].label)
    try:
        report = d.run()
    except KeyboardInterrupt:
        print(f"\nInterrupted. Resume with: debate resume {d.dir}", file=sys.stderr)
        return 130
    print(f"\nReport: {report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
