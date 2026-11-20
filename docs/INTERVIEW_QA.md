# Interview questions and answers

Each answer points to code (file and function) and, where it helps, a result (file and number).
Numbers marked "simulated" come from the deterministic fake models.

**1. What does calibra-eval do, in one breath?**
It runs evals offline from saved model answers, then checks its own LLM judge against answers
whose truth a checker already knows. See `src/calibra_eval/suite.py` (`run_eval_suite`,
`run_judge_suite`).

**2. Why does kappa beat percent agreement?**
Percent agreement counts matches, including lucky ones. A judge that says "correct" to everything
agrees 50% of the time on a balanced set and has learned nothing. Kappa subtracts the agreement
you would get by chance from each rater's base rates: `(po - pe) / (1 - pe)`. That judge gets
kappa 0. The test `test_always_correct_judge_has_kappa_zero` in `tests/test_judge.py` shows
exactly that. Code: `stats.cohen_kappa`.

**3. What did the simulated judge score?**
Agreement 0.764 and kappa 0.528 on 72 cases (`results/judge_calibration.json`, simulated, seed 1).
Kappa near 0.5 means moderate agreement beyond chance.

**4. Why do paired differences give tighter intervals?**
Two models answer the same questions. Some questions are hard for both. The paired method works
on the per-question difference, so the shared difficulty cancels out. Its variance is
`var(a) + var(b) - 2 cov(a, b)`. When the scores correlate, the covariance term shrinks it.
In `results/code_tasks.json` the strong minus weak gap is +0.325. The paired SE is 0.063 and the
unpaired SE is 0.093, with a correlation of 0.641 (simulated). Code: `stats.paired_difference`.

**5. How do fixtures keep tests deterministic?**
Every model request is turned into canonical JSON and hashed with SHA-256 (`canon.request_key`).
The response is saved under that key (`fixtures.FixtureStore`). Replay mode only reads. It never
calls a model and fails loudly on a missing key. The same request always gives the same bytes.
`scripts/replay_twice.sh` replays every suite twice and compares the JSON byte for byte.

**6. Why canonical JSON for the key?**
`{"a":1,"b":2}` and `{"b":2,"a":1}` are the same request. Without sorted keys they hash
differently and replay misses. `scripts/mutation_check.py` turns off `sort_keys` and the fixture
test fails.

**7. How is the position bias probe built?**
Each question has one right and one wrong answer. The judge sees them as A then B, and again as
B then A (`judge.run_calibration`). An unbiased judge picks the same answer both times and picks
A half the time. The simulated judge picked A 0.667 of the time and gave the same pick after a
swap only 0.500 of the time (`results/judge_calibration.json`, simulated).

**8. And the verbosity probe?**
The judge grades each answer twice: as written, and with a neutral paragraph added that carries
no information (`judge.PADDING`). For wrong answers, the simulated judge's accept rate went from
0.333 to 0.639 with padding, a paired gain of +0.306 (simulated).

**9. Where do the judge's errors come from?**
The simulated judge reads the last number in a math answer and runs only the visible code tests
(`fake.belief`). So "Final answer: 85 (my first try gave 83)" looks wrong to it, and code with a
bug that only a hidden test catches looks right. All 6 code answers with hidden-test bugs fooled
it. The README lists every error.

**10. How do you know the statistics code is right?**
`tests/reference/` holds values worked out by hand, with the arithmetic in
`HAND_CALCULATIONS.md`: a 2 by 2 kappa of 0.4, a 3 label kappa, seven pass@k values, a standard
error and a paired SE. `scripts/mutation_check.py` breaks the code in four ways and each break
fails a test.

**11. Why is pass@k computed with the unbiased formula?**
With n samples and c correct, `1 - C(n-c, k) / C(n, k)` is the exact chance that a random set of
k samples holds a correct one. The shortcut `1 - (1 - c/n)^k` assumes sampling with replacement
and is biased. Code: `stats.pass_at_k`.

**12. Why is the question the unit for the standard error?**
Samples of the same question are not independent. Miller's paper says to average per question
first and then take the SE over questions. `stats.pass_at_k_summary` and `suite.run_eval_suite`
do that.

**13. Why a percentile bootstrap?**
It needs no formula for kappa's variance and it works for any statistic. With a fixed seed it is
repeatable. `test_bootstrap_close_to_normal_interval_for_large_bernoulli` checks it against the
normal interval within 0.01. Code: `stats.bootstrap_ci`.

**14. Why build your own JSON schema checker?**
The brief allows numpy as the only runtime dependency. Five keywords cover the extraction
suite. `schema.validate` is about 40 lines.

**15. What would you do next?**
Record a real judge on a free provider (`examples/judge_calibration/suite.real.toml`), add a
self-enhancement probe with two model families, and export traces with the OpenTelemetry GenAI
conventions. See `docs/PROPOSALS.md`.

**16. What are the honest limits today?**
Every number so far comes from simulators, because no provider was reachable from the build
machine. 72 cases give a kappa interval about 0.36 wide. Fake-model tokens are word counts.
