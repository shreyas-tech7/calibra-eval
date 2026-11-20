# Contributing

Thanks for your interest. calibra-eval stays small on purpose, so please read this first.

## Ground rules

- Keep numpy as the only runtime dependency. Use the standard library for the rest.
- Tests run offline. `tests/conftest.py` fails any test that opens a non-local connection.
- Never edit `tests/reference/` values to make a test pass. Fix the code. If a reference is
  wrong, show the hand calculation in `tests/reference/HAND_CALCULATIONS.md`.
- Never type numbers into the README. Run `calibra readme` and commit the result.
- Use synthetic or public data only in cases and fixtures.

## Workflow

```bash
./init.sh                          # venv, install, ruff, all tests
.venv/bin/calibra run examples/*/suite.toml
.venv/bin/calibra readme
.venv/bin/python scripts/check_links.py
gitleaks git --pre-commit --redact --staged   # or: pre-commit install
```

Write a failing test first, then the smallest change that makes it pass. One change per
pull request. The CI job runs the same steps as `./init.sh`.

## Adding fixtures

Record with `calibra run --record <suite.toml>` against a free provider. Send only synthetic
or public text, because some free tiers can train on prompts. Commit the fixtures file so that
replay works for everyone.
