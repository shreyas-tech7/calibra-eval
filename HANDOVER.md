# Hand-off: calibra-eval v0.1.0-rc1

## 1. Status

DONE-WITH-BLOCKERS on branch `claude/build-calibra-eval`. The release commit is `1129e348b2925e8540d600a6e0ad90685049e291`. The commits after it only record the SHA and these notes. The code is finished and every test passes. The real-model run is blocked because no free provider could be reached from the build machine.

## 2. Done means

| # | Item | State | Evidence |
| --- | --- | --- | --- |
| 1 | `./init.sh` installs and runs every test offline | true | 92 tests pass in a fresh clone. A socket guard in `tests/conftest.py` blocks the network. |
| 2 | Stats checked against hand-computed values | true | `tests/reference/reference_values.json`, `HAND_CALCULATIONS.md`, `test_stats_reference.py`. An outside agent redid three values by hand. |
| 3 | Replay writes byte-identical JSON twice | true | `scripts/replay_twice.sh`. Also checked on Python 3.11 with the pinned numpy. |
| 4 | One recorded run on a free provider | blocked | BLOCKERS.md B1. Fallback: fake models. Steps: HUMAN_STEPS step 6. |
| 5 | Real judge report on 60+ cases | blocked | Same blocker. The fake judge report runs on 72 cases. `suite.real.toml` is ready. |
| 6 | README table made by a script | true | `calibra readme --check`. A hand edit makes two tests fail. |
| 7 | Quality bar complete | true | `tests/test_repo_quality.py`, `scripts/check_links.py` (0 errors), docs/RELEASE_CHECK.md. |

## 3. Results

All numbers come from simulated models (`fake:...`), seed 1, recorded on 2026-11-20. They show that the pipeline works. They say nothing about any real model.

- `results/code_tasks.json`: coder-strong 0.900 [0.800, 0.975], coder-weak 0.575 [0.412, 0.725]. Paired difference +0.325.
- `results/json_extract.json`: extractor 0.883 [0.800, 0.967].
- `results/judge_calibration.json`: judge-sim on 72 cases. Agreement 0.764 [0.667, 0.848], kappa 0.528 [0.337, 0.698], 0 unreadable verdicts. Position consistency 0.500. Padding raised the rate of accepted wrong answers by 0.306.
- `results/seed2/` repeats the run with seed 2.

## 4. Blockers

- **B1, no model provider.** Groq and OpenRouter returned a 403 through the proxy. I built deterministic fake models and recorded fixtures for them. Manual step: HUMAN_STEPS step 6.
- **B2, no GitHub.** I pushed to a local bare remote and made a bundle. Manual step: HUMAN_STEPS step 1.
- **B3, skills could not be installed.** I applied the Ponytail and humanizer rules by hand. A separate reviewer agent stood in for `ponytail-review`.
- **B4, blocked hosts.** osv and semgrep could not be reached. gitleaks, pip-audit, actionlint and ruff S ran instead.

## 5. Decisions

- Provider: took the brief's fake-model fallback after Groq and OpenRouter both returned a 403.
- Standard error uses ddof=1, and the bootstrap is a percentile bootstrap with 2000 resamples and a fixed seed.
- Judge labels come from the checkers, not from opinion: 36 questions, 72 cases, 36 pairs.
- An unreadable judge verdict counts against the judge, so a broken judge can never look good.
- numpy is pinned, so the committed results replay byte for byte.

## 6. Human steps

The full list with commands is in `docs/HUMAN_STEPS.md`.

1. Create the private repo `shreyas-tech7/calibra-eval`, clone the bundle and push every branch.
2. Check that CI is green.
3. Open the pull request, read the diff and merge it with a merge commit.
4. Tag `v0.1.0-rc1` on the release commit.
5. Run the secret scan once more.
6. Add a free provider key and record the real judge run.
7. Decide whether BUILD_PROMPT.md stays public, then make the repo public.
8. Fill in the About box, upload the social preview, turn on Pages and pin the repo.
9. Publish to PyPI, if you want to.

`docs/handoff/COWORK_PROMPT.md` covers the free browser steps that can be undone.

## 7. Check first

1. Read the diff, mainly `src/calibra_eval/stats.py` and `judge.py`.
2. Check two values in `tests/reference/HAND_CALCULATIONS.md` by hand.
3. Look at the first real judge run before you trust any judge number.

## 8. Plain brief

calibra-eval tests AI models on tasks whose right answers are already known, and it tells you how sure you can be of each score. Cases go in. A runner sends them to a model or to your code, and checkers mark each answer right or wrong. The statistics part adds error bars. The judge part measures whether an AI grader agrees with the known answers, and whether answer order or extra length fools it. Each model reply is saved, so anyone can rerun it offline and get the same bytes. A script writes the README tables from the saved results.

## 9. Resume launcher

Read docs/build/BUILD_PROMPT.md and follow it. Resume from PROGRESS.md on branch claude/build-calibra-eval. Do not ask questions. Do not stop until every Done-means item is true or blocked with a fallback.

## 10. Session link

https://claude.ai/code/session_01HXAvztqgc2cxMsM6oDuM8f
