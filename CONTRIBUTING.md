# Contributing to Syzetetes

Issues and pull requests are welcome.

## License of contributions

Syzetetes is licensed under the [PolyForm Noncommercial 1.0.0](LICENSE) license. By submitting a
contribution (code, documentation, examples, or anything else) you agree that:

1. your contribution is licensed to the project under the same license as the project; and
2. you grant Narbeh Mirzaei a perpetual, worldwide, irrevocable, royalty-free right to use, modify,
   distribute and **relicense** your contribution under any terms, including commercial ones.

Point 2 exists so that the project can later be offered under a different license (for example a
commercial one) without having to track down every contributor. If you cannot agree to it, please say so
in the pull request instead of submitting the change.

## Engineering rules

- **The debaters stay symmetric.** The only difference between Claude's and Codex's prompts is who they
  are told they are. Do not give one side a hint the other does not get.
- **The ledger is the single source of truth.** Verdict sections in the report are rendered from it,
  never from free prose alone.
- **Every new flag gets a spec key**, a comment in the `syzetetes init` template, and a wizard question.
- **Engine changes get a fake-agent test** in the style of `tests/test_engine.py`. No test may call a real
  CLI, Jev, or the network.
- **Examples move with the product.** A change to a spec key, command, pause trigger, model role or
  report format updates the README recipes, the files under `examples/`, and `example-report.md` in the
  same commit. `tests/test_examples.py` enforces most of this.
- Run `.venv/bin/python -m pytest -q` before opening a pull request.
