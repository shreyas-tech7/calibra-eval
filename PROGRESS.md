# Progress

## Done (flags true in feature_list.json)
- F01 to F14 and F17 to F21: init.sh, network guard, cases and checkers, targets, runner,
  record and replay, statistics with hand references, judge calibration, bias probes, cost,
  reports, README generator, example suites, byte-identical replay, GitHub Action and
  workflows, quality bar, study-later kit, release check, release candidate and hand-off.
- Mutation check: 7 of 7 deliberate bugs caught (`scripts/mutation_check.py`).
- Seed 2 rerun in results/seed2/.
- Release check: reviewer and outside-check agents ran. Every must-fix and should-fix item was
  fixed. See docs/RELEASE_CHECK.md.
- Release commit: 1129e348b2925e8540d600a6e0ad90685049e291. HANDOVER.md has the final report.

## Next
- Shreyas: docs/HUMAN_STEPS.md, starting with step 1 (create the GitHub repo, push the bundle).
- After a provider key exists: HUMAN_STEPS step 6, then set F15 and F16 true.
- Small leftover items: docs/PROPOSALS.md, "Small fixes left from the release check".

## Blocked
- F15 and F16: no free provider reachable (BLOCKERS.md B1). Fallback done: fake model.

## Last ./init.sh
- 2026-11-20: 92 passed, ruff clean, fresh clone included.
