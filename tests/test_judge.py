from pathlib import Path

import pytest

from calibra_eval.judge import (
    PADDING,
    JudgeCase,
    load_judge_cases,
    parse_pairwise,
    parse_pointwise,
    run_calibration,
)
from calibra_eval.targets import Output

CASES = load_judge_cases(Path(__file__).parent.parent / "examples/judge_calibration/judge_cases.jsonl")


TRUTH = {(c.question, c.candidate): c.label for c in CASES}


def oracle(prompt: str) -> Output:
    """Grades with the ground truth: a perfect judge. The same answer text can be right for one
    question and wrong for another, so the key is (question, answer)."""
    if "Answer A:\n" in prompt:
        q = prompt.split("Question:\n")[1].split("\n\nAnswer A:\n")[0]
        a = prompt.split("Answer A:\n")[1].split("\n\nAnswer B:\n")[0]
        return Output("A" if TRUTH[(q, a)] else "B")
    q = prompt.split("Question:\n")[1].split("\n\nAnswer:\n")[0]
    ans = prompt.split("Answer:\n")[1].split("\n\nReply with")[0].replace(PADDING, "")
    return Output("CORRECT" if TRUTH[(q, ans)] else "INCORRECT")


def test_parsers():
    assert parse_pointwise("CORRECT.") is True
    assert parse_pointwise("incorrect") is False
    assert parse_pointwise("maybe") is None
    assert parse_pairwise(" B ") == "B"
    assert parse_pairwise("Answer A") == "A"
    assert parse_pairwise("neither") is None


def test_enough_cases_with_ground_truth():
    assert len(CASES) >= 60
    assert sum(c.label for c in CASES) == len(CASES) // 2


def test_perfect_judge_has_kappa_one_and_no_bias():
    rep, calls = run_calibration(CASES, oracle, seed=1, workers=2, n_boot=200)
    assert rep["calibration"]["agreement"]["value"] == 1.0
    assert rep["calibration"]["kappa"]["value"] == 1.0
    assert rep["errors"] == []
    assert rep["position_probe"]["consistency"]["value"] == 1.0
    assert rep["position_probe"]["picks_A_rate"]["value"] == 0.5
    assert rep["verbosity_probe"]["wrong_padded_minus_raw"]["mean_diff"] == 0.0
    assert len(calls) == 2 * len(CASES) + 2 * rep["n_pairs"]


def test_always_correct_judge_has_kappa_zero():
    """Broken case: percent agreement alone says 0.5 here and hides that the judge learned nothing."""
    rep, _ = run_calibration(CASES, lambda p: Output("A" if "Answer A" in p else "CORRECT"),
                             seed=1, n_boot=200)
    assert rep["calibration"]["agreement"]["value"] == 0.5
    assert rep["calibration"]["kappa"]["value"] == 0.0


def test_bias_probe_position_catches_always_a():
    """Broken case: a judge that always answers A scores 50% pairwise accuracy and looks random."""
    def judge(p):
        return Output("A") if "Answer A:\n" in p else oracle(p)

    rep, _ = run_calibration(CASES, judge, seed=1, n_boot=200)
    pos = rep["position_probe"]
    assert pos["picks_A_rate"]["value"] == 1.0
    assert pos["consistency"]["value"] == 0.0
    assert pos["accuracy_gap"]["mean_diff"] == 1.0


def test_bias_probe_verbosity_catches_length_lean():
    def judge(p):
        if "Answer A:\n" not in p and PADDING in p:
            return Output("CORRECT")
        return oracle(p)

    rep, _ = run_calibration(CASES, judge, seed=1, n_boot=200)
    v = rep["verbosity_probe"]
    assert v["accept_wrong_raw"]["value"] == 0.0
    assert v["accept_wrong_padded"]["value"] == 1.0
    assert v["wrong_padded_minus_raw"]["mean_diff"] == 1.0
    assert v["right_padded_minus_raw"]["mean_diff"] == 0.0


def test_invalid_verdict_counts_against_the_judge():
    rep, _ = run_calibration(CASES[:4], lambda p: Output("no idea"), seed=1, n_boot=50)
    assert rep["invalid_verdicts"] == 4 * 2 + 2 * 2
    assert rep["calibration"]["agreement"]["value"] == pytest.approx(0.5)


def test_duplicate_ids_rejected(tmp_path):
    p = tmp_path / "j.jsonl"
    row = '{"id":"x","pair_id":"p","task_type":"math","question":"q","candidate":"c","label":true}\n'
    p.write_text(row * 2)
    with pytest.raises(ValueError):
        load_judge_cases(p)
    assert JudgeCase("x", "p", "math", "q", "c", True).label
