# Decisions

One line per choice: the options weighed and the reason.

- 2026-11-20 Name: kept `calibra-eval` (options: calibra-eval, judgelab). PyPI `calibra-eval` 404, PyPI `calibra_eval` 404, npm `calibra-eval` 404 on 2026-11-20. Web search was not run because the session lacks a working web search for this check, so a GitHub name clash is not ruled out. Repo name already matches, so no rename step.
- 2026-11-20 Remote: this session has no working GitHub token. The coordinator gave a local bare Git remote as `origin` (options: real GitHub, local remote). Used the local remote. Moving it to GitHub is human step 1.
- 2026-11-20 Branch: `claude/build-calibra-eval`, as the coordinator brief says.
- 2026-11-20 Build backend: setuptools with a src layout (options: hatchling, setuptools, flit). setuptools is the most common and needs nothing extra.
- 2026-11-20 Python: VM has 3.13. CI tests on 3.11 as the brief says. Code uses only 3.11 features.
- 2026-11-20 Provider: Groq and OpenRouter both answer `CONNECT tunnel failed, response 403` from this VM (options: wait, other provider, fake model). Took the brief's fallback: finish with the fake model, leave F15 and F16 false.
- 2026-11-20 Fixture store: one JSON Lines file per suite, sorted by key on save (options: one file per key, one JSONL). One sorted file keeps diffs small and the repo tidy with about 500 fixtures.
- 2026-11-20 Standard error: sample standard deviation with ddof=1 divided by sqrt(n) (options: ddof=0, Bernoulli p(1-p)/n). ddof=1 is the usual unbiased choice and matches Miller's general formula. For pass@k and multi-sample cases the unit is the question, so SE is over questions (Miller's clustering advice).
- 2026-11-20 Bootstrap: percentile bootstrap, 2000 resamples, numpy default_rng(seed) (options: BCa, percentile). Percentile is simple and enough at this sample size. Seed 1 by default as the brief says.
- 2026-11-20 Fake judge: a deterministic simulator, not a model. It solves math with a safe arithmetic evaluator, checks code only against the visible example tests in the prompt, adds seeded noise and has a designed tie-break toward answer A and a designed lean toward long answers. Its errors are partly natural (hidden tests) and partly designed. The README labels every fake-judge number as simulated.
- 2026-11-20 Judge cases: 36 questions (24 math, 12 code), each with one right and one wrong candidate, 72 pointwise cases and 36 pairs. Labels come from the checkers, not from opinion.
- 2026-11-20 Social preview PNG: written with a stdlib PNG encoder and a hand-coded 5x7 bitmap font (options: Pillow, matplotlib, stdlib). The brief allows no new dependency.
- 2026-11-20 Skills: `npx skills add` was refused by this session's permission system. Did not retry in another form. Used the superpowers skills already present and applied the Ponytail rules (small, plain, no extra layers) by hand.
- 2026-11-20 Line length: 110 (options: 88, 100, 110). Fewer wrapped lines in the statistics and report code.
- 2026-11-20 Commits: the first session committed core modules as one initializer commit (options: one commit per feature, grouped). The modules were written in one pass before the tests, then each key test was proved with a deliberate mutation in scripts/mutation_check.py. Later work uses one area per commit.
- 2026-11-20 Network guard test target: 192.0.2.1, a TEST-NET documentation address (options: a public IP, TEST-NET). The mutation check then never touches a real host.
- 2026-11-20 gitleaks: added .gitleaks.toml that extends the default rules and allows only the exact pattern key":"<64 hex>" (options: skip fixture paths, allow the pattern). Skipping paths would hide a real secret in a fixture. A planted key in a test file is still caught.
- 2026-11-20 Unparseable judge verdicts count against the judge: they are scored as the opposite of the truth (options: drop them, count as 'not correct', count against the judge). An earlier version counted them as 'not correct'. The release review showed that this earns free agreement on wrong answers and makes a broken judge look position-consistent, so it was changed. The README shows how many there were.
- 2026-11-20 numpy is pinned in constraints.txt (options: a range, a pin, a lock file). NumPy does not promise the same random stream across versions, and the committed results must replay byte for byte.
