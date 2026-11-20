# Plan: calibra-eval

The brief in docs/build/BUILD_PROMPT.md Part 2 is the spec. This plan turns it into steps.
Each step lists the files, the test that proves it and the feature id in feature_list.json.

## Goal
A library and `calibra` command that run evals offline from fixtures and report how far their
own LLM judge can be trusted, with honest statistics.

## Architecture
Cases (JSONL) and a suite (TOML) go into the runner. The runner calls a target through a cache.
Model calls go through the fixture store. Checkers score each output. An optional judge pass
grades answers whose truth the checkers already know. The stats module adds intervals. Reports
write a terminal table, JSON, HTML, a pull request comment and the README tables.

## Steps
1. Initializer: memory files, init.sh, license, gitignore, secret scan hook. (F01)
2. Network guard in tests/conftest.py and its test. (F02)
3. Cases loader, small JSON schema checker, four checkers. Tests: test_cases, test_schema,
   test_checkers. (F03)
4. Targets: Python function, shell command, model. Fake models and the OpenAI-compatible
   adapter on urllib with 429 backoff. Tests: test_targets, test_adapter. (F04)
5. Runner with ThreadPoolExecutor and a disk cache. Test: test_runner. (F05)
6. Fixture store and CachedModel record or replay. Test: test_fixtures. (F06)
7. Stats: mean and SE, normal and bootstrap intervals, pass@k, paired difference, kappa.
   Hand values in tests/reference/. Test: test_stats_reference. (F07)
8. Judge calibration and bias probes. Test: test_judge. (F08, F09)
9. Cost and latency summary with an optional price table. Test: test_cost. (F10)
10. Reports and README generator. Tests: test_report, test_readme_sync. (F11, F12)
11. Example suites: code_tasks (unit tests), json_extract (schema), judge_calibration (72 cases).
    Build scripts write the cases. Judge cases are committed before the first judge run. (F13)
12. Record fixtures with the fake models, then replay twice and compare bytes. (F14)
13. Record mode on a free provider. Blocked on this VM (B1). Exact steps go to HUMAN_STEPS. (F15, F16)
14. CI workflow and the PR comment action. Test renders the comment body. actionlint. (F17)
15. Quality bar, study-later kit, release check, hand-off. (F18 to F21)

## Assumptions
- No provider is reachable, so fake models stand in. Every fake number is labeled simulated.
- The fake judge is a simulator with partly natural and partly designed errors (DECISIONS.md).
- pass@k uses n = 5 samples per code task, with k = 1 and k = 5.
- The unit of analysis is the question. Samples are averaged per question first.
