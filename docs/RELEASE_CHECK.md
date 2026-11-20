# Release check for v0.1.0-rc1

Run on 2026-11-20 on the build machine (Python 3.13, numpy 2.4.4). Section 11 of the build prompt sets the steps.

## 1. Code review

The `ponytail-review` skill could not be installed here (see BLOCKERS.md B3). In its place, a separate reviewer agent that did not write the code read the whole diff. It found 2 must-fix items and 6 should-fix items. Here is what happened to each.

| Finding | Severity | What we did |
| --- | --- | --- |
| `.gitignore` line `build/` hid `docs/build/BUILD_PROMPT.md`, so a fresh clone failed 2 tests | must-fix | Fixed. The line is now `/build/` and the file is committed. |
| An unreadable judge verdict counted as "wrong", which earned free agreement and made garbage output look position-consistent and immune to padding | must-fix | Fixed. An unreadable verdict now always counts against the judge. A judge that only prints garbage now scores 0 agreement and 0 consistency. The README table shows the count. |
| The disk cache served old output after you edited the target function | should-fix | Fixed. The cache key now holds a hash of the function's file. Shell targets are no longer cached. |
| One provider error lost every fixture recorded so far, and a rate limit lowered the pass rate | should-fix | Fixed. Fixtures save in a `finally` block. The adapter retries 5xx, dropped connections and timeouts. A provider error stops the run instead of failing the case. |
| A newer numpy could change the bootstrap stream and break byte-identical replay | should-fix | Fixed. `constraints.txt` pins numpy 2.4.4. Replay was checked byte-identical on Python 3.11 and 3.13. |
| The composite action installed the calling repo, failed on fork pull requests and posted a new comment each push | should-fix | Fixed. It installs from `github.action_path`, skips the post on forks and edits its last comment. |
| Model-written code inherited the caller's environment, including `LLM_API_KEY` | should-fix | Fixed in part. The code now gets only `PATH`. It is still not a sandbox, and the README Limits section says so. |
| "The answer is not correct." parsed as a pass | should-fix | Fixed. Only the first word counts, and it must be CORRECT or INCORRECT. |
| A shell target that crashed after printing the right output passed | nit | Fixed. A nonzero exit is now a target error. |
| Unused `__len__`, the dead `else 0.0` kappa branch, the Markdown re-parse for cost rows, the `seed*1000 + sample` collision at 1000 samples, `_pairs` not checking the question, `_file` depending on the current folder, error list cut at 12 rows, the wall-clock test, the weak kappa CI test, `sed` on the model id in `record.yml` | nit | Logged, not fixed. None of them changes a committed number. They are listed in docs/PROPOSALS.md for the next version. |

## 2. Security audit

Skipped, as the build prompt says. The project has no sign-in, personal data or payments. The review above and `ruff check --select S` cover it.

## 3. Tool results

| Tool | Result |
| --- | --- |
| `gitleaks git -v .` (full history) | no leaks found |
| `pip-audit` on the installed dependencies | no known vulnerabilities (calibra-eval itself is not on PyPI, so pip-audit skips it) |
| `actionlint` | no findings |
| `scripts/check_links.py` | 0 errors, 7 external links not checked (no network to them here) |
| `ruff check --select S` | 15 findings, all accepted (below) |
| `scripts/mutation_check.py` | 7 of 7 deliberate bugs caught |

Accepted `ruff --select S` findings:

- **S101** (`assert`) in `scripts/build_examples.py`: these asserts check the hand-written labels when the examples are rebuilt. They are meant to stop the script.
- **S311** (`random`) in `scripts/build_examples.py`: it makes synthetic data from a fixed seed. Nothing here needs crypto randomness.
- **S603** (`subprocess`) in `checkers.py`, `fake.py`, `targets.py`, `scripts/mutation_check.py` and two tests: every call passes a list of arguments, no shell, and a timeout. Running candidate code is the point of the unittest checker. The README Limits section says it is not a sandbox.
- **S310** (`urlopen`) in `adapter.py`: the constructor rejects any scheme other than `http` and `https`, and a test covers that.

## 4. Humanizer pass

The humanizer skill could not be installed (BLOCKERS.md B3). The same rules were applied by hand to `README.md` and `docs/*.md`: active voice, plain words, no em dashes or semicolons, no filler. Every fact, number, name and code block stayed the same. The README numbers come from the generator, so the pass could not change them.

## 5. Outside check

A separate agent cloned the repo fresh, ran `./init.sh` and checked each Done-means item with its own commands. It edited no file.

| Item | First result | After fixes |
| --- | --- | --- |
| 1. `./init.sh` passes offline | fail: 2 tests, because of the `.gitignore` bug | pass: 92 tests in a fresh clone |
| 2. Stats match hand-computed values | pass. It redid three values by hand. | pass |
| 3. Replay is byte-identical | pass | pass |
| 4. Recorded run on a free provider | blocked, documented (B1) | blocked, documented |
| 5. Real judge on 60+ cases | blocked, documented (B1). Fake judge report is honest about being simulated. | blocked, documented |
| 6. README table comes from a script | pass. A hand edit made `--check` and two tests fail. | pass |
| 7. Quality bar | fail: the link checker missed BUILD_PROMPT.md | pass |

It also found that `calibra run --record` with no `LLM_BASE_URL` printed a traceback. That now prints one error line and exits 2, with a test.

## 6. Final state

`git status` is clean. Each `passes` flag in `feature_list.json` matches a passing check. F15 and F16 stay false because they need a real provider.
