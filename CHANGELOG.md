# Changelog

## v0.1.0-rc1 (2026-11-20)

First release candidate.

- Cases in JSON Lines, suites in TOML. Checkers: exact, regex, JSON schema (built in), unit test.
- Targets: Python function, shell command, OpenAI-compatible model over urllib, fake models.
- Runner with parallel workers and a disk cache.
- Record and replay with fixtures keyed by SHA-256 of the canonical request JSON.
- Statistics: mean and SE, normal and bootstrap intervals, pass@k with intervals, paired
  differences, percent agreement and Cohen's kappa. Hand-computed reference tests.
- Judge calibration with position and verbosity bias probes.
- Cost and latency summary with an optional price table.
- Reports: terminal, JSON, static HTML, pull request comment, generated README tables.
- Three example suites with fixtures. GitHub Action for the PR comment.
- Release check fixes: unreadable judge verdicts count against the judge, first-word verdict
  parsing, cache keyed by file contents, retries and saved fixtures on provider errors, numpy pin.
- Not done: a real-model run (no provider was reachable from the build machine).

Release commit: 1129e348b2925e8540d600a6e0ad90685049e291

The commits after it only record this SHA and the hand-off notes. Tag this commit.
