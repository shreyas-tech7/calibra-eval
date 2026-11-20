"""Prove that the reference tests and guards catch broken code.

Each mutation breaks one line in a temp copy of the repo. The matching test must fail on the
mutant and pass on the original. Run: .venv/bin/python scripts/mutation_check.py
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MUTATIONS = [
    ("kappa forgets chance agreement", "src/calibra_eval/stats.py",
     "    return (po - pe) / (1.0 - pe)", "    return po", "tests/test_stats_reference.py"),
    ("standard error with ddof=0", "src/calibra_eval/stats.py",
     "x.std(ddof=1)", "x.std(ddof=0)", "tests/test_stats_reference.py"),
    ("pass@k uses (c/n) shortcut", "src/calibra_eval/stats.py",
     "    return 1.0 - math.comb(n - c, k) / math.comb(n, k)",
     "    return 1.0 - (1 - c / n) ** k", "tests/test_stats_reference.py"),
    ("bootstrap without replacement", "src/calibra_eval/stats.py",
     "rows[rng.integers(0, n, n)]", "rows[rng.permutation(n)]", "tests/test_stats_reference.py"),
    ("network guard removed", "tests/conftest.py",
     '    monkeypatch.setattr(socket.socket, "connect", _guarded_connect)\n', "",
     "tests/test_network_guard.py::test_guard_blocks_remote_host"),
    ("fixture key without sorted keys", "src/calibra_eval/canon.py",
     "sort_keys=True", "sort_keys=False", "tests/test_fixtures.py"),
    ("README number typed by hand", "README.md",
     "<!-- calibra:results:start -->\n", "<!-- calibra:results:start -->\nPass rate 0.999\n",
     "tests/test_readme_sync.py"),
]


def run_pytest(repo: Path, target: str) -> int:
    py = ROOT / ".venv" / "bin" / "python"
    return subprocess.run([str(py), "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", target],
                          cwd=repo, capture_output=True, text=True, timeout=600,
                          env={"PYTHONPATH": str(repo / "src"), "PATH": "/usr/bin:/bin"}).returncode


def main() -> int:
    failures = 0
    for name, rel, old, new, test in MUTATIONS:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns(".venv", ".git", "*.pyc"))
            target = repo / rel
            text = target.read_text(encoding="utf-8")
            if old not in text:
                print(f"SKIP-ERROR {name}: pattern not found in {rel}")
                failures += 1
                continue
            clean = run_pytest(repo, test)
            target.write_text(text.replace(old, new, 1), encoding="utf-8")
            mutant = run_pytest(repo, test)
            ok = clean == 0 and mutant != 0
            failures += not ok
            print(f"{'CAUGHT' if ok else 'MISSED'} {name}: clean exit {clean}, mutant exit {mutant}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
