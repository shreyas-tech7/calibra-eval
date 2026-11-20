# calibra-eval: project context

## What it is
A small Python library and `calibra` command. It runs agent evals offline from recorded
fixtures, then measures how far its own LLM judge can be trusted (agreement, Cohen's kappa,
position bias, verbosity bias) with bootstrap intervals and paired statistics.

## Status
See PROGRESS.md and feature_list.json. No free provider was reachable from the build VM, so all
results so far come from deterministic fake models (simulators). Real-model record mode is a
human step.

## Stack
Python 3.11+, standard library, numpy, pytest, ruff. TOML via tomllib. urllib for HTTP.

## Commands
- `./init.sh`: venv, install, ruff, all tests offline.
- `.venv/bin/calibra run examples/*/suite.toml`: replay every example suite into results/.
- `.venv/bin/calibra run --record <suite.toml>`: call the model for missing fixtures.
- `.venv/bin/calibra readme` and `calibra readme --check`: README tables from results/.
- `.venv/bin/calibra report --html docs/index.html`: static results page.
- `.venv/bin/calibra pr-comment --out comment.md`: pull request comment body.
- `bash scripts/replay_twice.sh`: proves byte-identical JSON across two replays.
- `.venv/bin/python scripts/mutation_check.py`: proves the key tests catch broken code.
- `.venv/bin/python scripts/check_links.py`: link checker.

## Layout
- `src/calibra_eval/`: canon (hashing), cases, checkers, schema, fake, adapter, fixtures,
  targets, runner, stats, judge, cost, suite, report, readme, cli.
- `examples/code_tasks`, `examples/json_extract`, `examples/judge_calibration`: suites,
  cases, fake answer banks and fixtures.
- `results/`: result JSON written by `calibra run`. README numbers come from here.
- `tests/`: offline tests. `tests/reference/` holds hand-computed values.
- `scripts/`: case builders, README and preview generators, checks.
- `docs/`: plan, walkthrough, interview Q and A, human steps, demo page.

## Rules
- Never type numbers into the README. Run `calibra readme`.
- Never change `tests/reference/` values to make a test pass.
- Tests run offline. `tests/conftest.py` blocks non-local sockets.
- Fixture key = SHA-256 of canonical request JSON (sorted keys, no spaces).
- Seed 1 by default. Rerun results that look too good with seed 2.
- No new dependencies beyond numpy, pytest and ruff.

## Skills that fit
superpowers test-driven-development, systematic-debugging, verification-before-completion,
requesting-code-review.

## Do not read
`.venv/`, `examples/*/fixtures.jsonl` (large, machine written), `logs/`, `graphify-out/`.
