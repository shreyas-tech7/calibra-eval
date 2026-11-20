#!/usr/bin/env bash
# Write docs/DEMO.md from a real terminal session. Every output block is captured, not typed.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=docs/DEMO.md
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
run() {
  echo '```console'
  echo "\$ $*" | sed "s|$TMP|/tmp/demo|g"
  ( eval "$@" ) 2>&1 | sed "s|$TMP|/tmp/demo|g"
  echo '```'
  echo
}
{
  echo "# Demo"
  echo
  echo "A real terminal session, captured by \`scripts/make_demo.sh\` on $(date -u +%Y-%m-%d)"
  echo "($(python3 -c 'import platform;print(platform.python_version())') on $(uname -s))."
  echo "Nothing here needs a key or the network. Models named \`fake:...\` are simulators."
  echo
  echo "## Version"
  echo
  run .venv/bin/calibra --version
  echo "## Replay the judge calibration suite from fixtures"
  echo
  run .venv/bin/calibra run --out "$TMP" examples/judge_calibration/suite.toml
  echo "## Replay the code suite and compare two models with paired statistics"
  echo
  run .venv/bin/calibra run --out "$TMP" examples/code_tasks/suite.toml
  echo "## Replay is byte-identical"
  echo
  run bash scripts/replay_twice.sh
  echo "## The README tables match the result files"
  echo
  run .venv/bin/calibra readme --check
  echo "## A missing fixture fails loudly in replay mode"
  echo
  run "cp -r examples/json_extract $TMP/je && : > $TMP/je/fixtures.jsonl && (.venv/bin/calibra run --out $TMP $TMP/je/suite.toml 2>&1 | tail -1) || true"
} > "$OUT"
echo "wrote $OUT"
