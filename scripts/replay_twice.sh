#!/usr/bin/env bash
# Replay every example suite twice from fixtures and check the JSON is byte-identical,
# both between the two runs and against the committed results/.
set -euo pipefail
cd "$(dirname "$0")/.."
CAL=.venv/bin/calibra
A=$(mktemp -d); B=$(mktemp -d)
trap 'rm -rf "$A" "$B"' EXIT
SUITES="examples/code_tasks/suite.toml examples/json_extract/suite.toml examples/judge_calibration/suite.toml"
$CAL run --out "$A" $SUITES > /dev/null
$CAL run --out "$B" --workers 1 $SUITES > /dev/null
status=0
for f in "$A"/*.json; do
  name=$(basename "$f")
  if cmp -s "$f" "$B/$name"; then echo "identical across runs: $name ($(sha256sum < "$f" | cut -c1-16))"; else echo "DIFFERENT across runs: $name"; status=1; fi
  if cmp -s "$f" "results/$name"; then echo "matches committed results/$name"; else echo "DIFFERS from committed results/$name"; status=1; fi
done
exit $status
