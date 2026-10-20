# Syzetetes: project rules

## Examples and docs move with the product
Any change to a spec key, a CLI command or flag, a pause trigger, a model role, or the report format must,
in the same commit:
1. update the README recipe(s) that show it, both the spec form and the flag form;
2. update every file under `examples/` that uses it (they must stay runnable as they are);
3. regenerate `example-report.md` from a real coded run if the report format changed;
4. keep `tests/test_examples.py` green: it loads every example under the current schema, checks that every
   file an example references exists, that the README links every example and only existing ones, and that
   `example-report.md` is in the current format.
Stale examples are a bug, not a docs chore. If an example cannot be kept runnable, delete it and its README link.

## Other rules
- The two debaters stay symmetric: the only difference between their prompts is who they are told they are.
- The ledger is the single source of truth; nothing in the report is rendered from free prose alone.
- Every new flag gets a spec key, a template comment, and a wizard question.
- Engine changes get a fake-agent test (`tests/test_engine.py` style); no test may call a real CLI or the network.
- Never delete a file the user created; only clean up what this session made.
