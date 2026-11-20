# Walkthrough

A tour of every file in plain English. One idea per sentence.

## The big picture

calibra-eval runs tests on AI answers. It saves every model answer to a file. Later runs read the
file instead of calling the model. That makes runs free and repeatable. It also tests the AI
judge. It gives the judge answers whose truth is already known. Then it counts how often the
judge is right.

## Top folder

- `README.md` is the front page. Its tables are written by a script, not by hand.
- `init.sh` sets everything up and runs every test. Run it first.
- `pyproject.toml` names the package, its one dependency (numpy) and the `calibra` command.
- `LICENSE` is the MIT license.
- `CHANGELOG.md` lists what changed in each release.
- `CONTRIBUTING.md` explains how to help.
- `action.yml` is a small GitHub Action. It replays the suites and writes a pull request comment.
- `.gitleaks.toml` tunes the secret scanner. It allows the fixture hashes and nothing else.
- `.pre-commit-config.yaml` runs the secret scanner before each commit.
- `.env.example` shows the settings for record mode. The real `.env` is never committed.
- `PROJECT_CONTEXT.md`, `CLAUDE.md`, `PROGRESS.md`, `feature_list.json`, `DECISIONS.md` and
  `BLOCKERS.md` are the build notes. They let a new agent session pick up the work.

## The package: `src/calibra_eval/`

- `canon.py` turns a request into canonical JSON (sorted keys, no spaces). Then it hashes it
  with SHA-256. That hash is the fixture key.
- `cases.py` reads cases from a JSON Lines file. Each line is one case. It rejects bad lines.
- `schema.py` is a tiny JSON schema checker. It knows `type`, `required`, `properties`, `items`
  and `enum`.
- `checkers.py` decides pass or fail. There are four checkers: exact, regex, JSON schema and unit
  test. The unit test checker runs code in a fresh Python process with a time limit.
- `adapter.py` talks to any OpenAI-compatible endpoint with `urllib`. It reads the key from an
  environment variable. It waits and retries on HTTP 429.
- `fake.py` holds the fake models. They are simulators, not AI. Each answer depends only on the
  request, so it never changes. The fake judge solves math with a safe calculator. It runs only
  the visible code examples, so hidden bugs fool it.
- `fixtures.py` stores and finds saved answers. Replay mode never calls a model. Record mode
  calls the model only for new requests.
- `targets.py` defines what gets tested: a Python function, a shell command or a model.
- `runner.py` runs a target over all cases with several threads. It keeps results in a fixed
  order. It caches non-model calls on disk.
- `stats.py` does the math: mean, standard error, bootstrap intervals, pass@k, paired
  differences, percent agreement and Cohen's kappa.
- `judge.py` runs the judge pass. It asks the judge about each answer, then again with padding,
  then in pairs with the order swapped.
- `cost.py` adds up tokens and timings. It adds dollars only if you give it a price table.
- `suite.py` reads a suite TOML file and ties everything together.
- `report.py` turns result files into tables: terminal, Markdown, HTML and the PR comment.
- `readme.py` rewrites the README tables between marker comments.
- `cli.py` is the `calibra` command: `run`, `report`, `readme` and `pr-comment`.

## Examples: `examples/`

- `code_tasks/` has 16 small Python tasks. Each has visible tests and hidden tests. Two fake
  models answer each task 5 times. `fake_bank.json` holds the right and wrong answers.
- `json_extract/` has 20 made-up order notes. The answer must match a schema and the truth.
- `judge_calibration/` has 72 graded answers: 24 math and 12 code questions, each with one right
  and one wrong answer. Checkers made the labels. `suite.real.toml` is ready for a real judge.
- Each `fixtures.jsonl` holds the saved fake-model answers.

## Results: `results/`

- One JSON file per suite. `calibra run` writes them. The README reads them.
- `results/seed2/` holds the rerun with seed 2.

## Tests: `tests/`

- `conftest.py` blocks network access in tests. `test_network_guard.py` proves it works.
- `reference/` holds hand-computed values and the notes that show the arithmetic.
- `test_stats_reference.py` compares the stats code to those values.
- `test_examples.py` replays every suite and compares it to the committed results.
- `test_readme_sync.py` fails if a README number does not match the results.
- `test_repo_quality.py` checks the README order, required files and writing rules.
- The other test files cover one module each.

## Scripts: `scripts/`

- `build_examples.py` writes the example cases and answer banks. It checks every label.
- `replay_twice.sh` replays all suites twice and compares the bytes.
- `mutation_check.py` breaks the code on purpose and checks that the tests notice.
- `check_features.py` runs the steps of every feature in `feature_list.json`.
- `check_links.py` checks links in Markdown and HTML files.
- `make_social_preview.py` draws `docs/social-preview.png`.
- `make_demo.sh` writes `docs/DEMO.md` from a real terminal session.

## Docs: `docs/`

- `index.html` is the results page. It opens from disk.
- `DEMO.md` is a real terminal transcript.
- `PLAN.md` is the build plan. `ENVIRONMENT.md` and `TOOLING.md` record the build machine.
- `INTERVIEW_QA.md` has questions and answers about the design.
- `HUMAN_STEPS.md` lists what only Shreyas can do. `handoff/COWORK_PROMPT.md` helps with it.
- `build/BUILD_PROMPT.md` is the prompt that drove the build.
- `GITHUB_ABOUT.md` has the repo description and topics.

## Workflows: `.github/workflows/`

- `ci.yml` runs `./init.sh`, the README check and the replay check on Python 3.11.
- `eval-comment.yml` posts the results table on each pull request.
- `record.yml` records a real judge run. It only runs when started by hand.
