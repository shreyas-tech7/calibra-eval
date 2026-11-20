"""The example suites replay from committed fixtures and match the committed results."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from calibra_eval.cases import load_cases
from calibra_eval.checkers import check
from calibra_eval.suite import run_suite

ROOT = Path(__file__).resolve().parent.parent
SUITES = ["code_tasks", "json_extract", "judge_calibration"]


@pytest.mark.parametrize("name", SUITES)
def test_replay_matches_committed_results(name):
    res = run_suite(ROOT / "examples" / name / "suite.toml", "replay")
    committed = json.loads((ROOT / "results" / f"{name}.json").read_text())
    assert json.loads(json.dumps(res, sort_keys=True)) == committed


def test_judge_report_has_60_plus_cases_and_both_probes():
    d = json.loads((ROOT / "results" / "judge_calibration.json").read_text())
    assert d["n_cases"] >= 60
    assert {"agreement", "kappa"} <= set(d["calibration"])
    assert "consistency" in d["position_probe"] and "wrong_padded_minus_raw" in d["verbosity_probe"]
    assert d["errors"], "the report must show real judge errors"


def test_code_bank_answers_score_as_labeled():
    """Every 'good' answer passes and every 'bad' answer fails its unit tests."""
    cases = {c.input: c for c in load_cases(ROOT / "examples/code_tasks/cases.jsonl")}
    bank = json.loads((ROOT / "examples/code_tasks/fake_bank.json").read_text())
    for prompt, entry in bank.items():
        c = cases[prompt]
        assert all(check(c.checker, g).passed for g in entry["good"])
        assert not any(check(c.checker, b).passed for b in entry["bad"])


def test_build_script_is_reproducible(tmp_path):
    """Rebuilding the cases from the script gives the committed files byte for byte."""
    import shutil

    repo = tmp_path / "r"
    for sub in ("scripts", "src"):
        shutil.copytree(ROOT / sub, repo / sub)
    subprocess.run([sys.executable, "-I", str(repo / "scripts/build_examples.py")], check=True,
                   timeout=300, capture_output=True)
    for rel in ("examples/code_tasks/cases.jsonl", "examples/json_extract/cases.jsonl",
                "examples/judge_calibration/judge_cases.jsonl"):
        assert (repo / rel).read_bytes() == (ROOT / rel).read_bytes(), rel
