# Proposals

Ideas that the brief does not list. Shreyas picks what gets built.

- Self-enhancement bias probe: judge answers from two model families with each family as judge.
- OpenTelemetry GenAI trace export (the brief's stretch item). Pin the semantic conventions
  version, because they are still marked as in development.
- A `calibra diff` command that compares two results files with paired statistics.
- Stratified bootstrap by task type, so math and code keep their share in every resample.
- Cluster bootstrap for suites with several samples per question.

## Small fixes left from the release check

The reviewer flagged these. None of them changes a committed number.

- Drop the unused `FixtureStore.__len__` and the `else 0.0` kappa branch that cannot run.
- Score bootstrap resamples with a single label carefully on small task-type subsets.
- Build cost rows once and reuse them, so a model name with `|` cannot break the table.
- Make the model request seed collision-free past 1000 samples.
- Check in `_pairs` that the right and wrong answers share a question, and warn on extra cases.
- Resolve `_file` paths against the results folder, so `readme --check` works from any folder.
- Say "and N more" when the judge error list is cut at 12 rows.
- Check the `record.yml` model input against a regex before `sed` writes it into TOML.
- Replace the wall-clock assert in `test_runner.py` and tighten the kappa CI test.
