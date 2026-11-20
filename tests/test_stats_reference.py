"""Statistics against hand-computed values in tests/reference/. Never edit those values to pass."""

import json
from pathlib import Path

import numpy as np
import pytest

from calibra_eval import stats

REF = json.loads((Path(__file__).parent / "reference" / "reference_values.json").read_text())


def _expand_2x2(t):
    judge = [1] * t["judge_yes_truth_yes"] + [1] * t["judge_yes_truth_no"] + \
            [0] * t["judge_no_truth_yes"] + [0] * t["judge_no_truth_no"]
    truth = [1] * t["judge_yes_truth_yes"] + [0] * t["judge_yes_truth_no"] + \
            [1] * t["judge_no_truth_yes"] + [0] * t["judge_no_truth_no"]
    return judge, truth


def test_kappa_2x2_matches_hand_value():
    """Broken case: a kappa that forgets chance agreement returns 0.7, not 0.4."""
    r = REF["kappa_2x2"]
    j, t = _expand_2x2(r["table"])
    assert stats.percent_agreement(j, t) == pytest.approx(r["percent_agreement"], abs=1e-12)
    assert stats.cohen_kappa(j, t) == pytest.approx(r["kappa"], abs=1e-12)


def test_kappa_3_labels_matches_hand_value():
    """Broken case: chance agreement from one rater's marginals only gives a different value."""
    r = REF["kappa_3x3"]
    x, y = [], []
    for a, b, n in r["pairs"]:
        x += [a] * n
        y += [b] * n
    assert stats.percent_agreement(x, y) == pytest.approx(r["percent_agreement"], abs=1e-12)
    assert stats.cohen_kappa(x, y) == pytest.approx(r["kappa"], abs=1e-12)


def test_kappa_single_label_edge():
    assert stats.cohen_kappa([1, 1, 1], [1, 1, 1]) == 1.0
    assert stats.cohen_kappa([1, 1], [0, 0]) == 0.0


@pytest.mark.parametrize("row", REF["pass_at_k"], ids=lambda r: f"n{r['n']}c{r['c']}k{r['k']}")
def test_pass_at_k_matches_hand_value(row):
    """Broken case: the naive estimate c/n for k=1 is fine, but (c/n)**k style shortcuts fail k>1."""
    assert stats.pass_at_k(row["n"], row["c"], row["k"]) == pytest.approx(row["value"], abs=1e-12)


def test_pass_at_k_rejects_bad_input():
    with pytest.raises(ValueError):
        stats.pass_at_k(3, 4, 1)
    with pytest.raises(ValueError):
        stats.pass_at_k(3, 1, 4)


def test_mean_se_matches_hand_value():
    """Broken case: ddof=0 gives 0.1530931, not 0.1636634."""
    r = REF["mean_se"]
    mean, se = stats.mean_se(r["values"])
    assert mean == pytest.approx(r["mean"], abs=1e-12)
    assert se == pytest.approx(r["se"], abs=1e-12)


def test_paired_difference_matches_hand_value():
    """Broken case: using the unpaired formula for the paired SE gives 0.3464, not 0.3162."""
    r = REF["paired_difference"]
    d = stats.paired_difference(r["a"], r["b"], seed=1, n_boot=200)
    assert d["mean_diff"] == pytest.approx(r["mean_diff"], abs=1e-12)
    assert d["se_paired"] == pytest.approx(r["se_paired"], abs=1e-12)
    assert d["se_unpaired"] == pytest.approx(r["se_unpaired"], abs=1e-12)


def test_bootstrap_repeatable_with_fixed_seed():
    # continuous data, because bootstrap means of 0/1 data sit on a grid and two seeds can tie
    data = np.linspace(0.0, 1.0, 37) ** 2
    a = stats.bootstrap_ci(data, np.mean, n_boot=500, seed=1)
    b = stats.bootstrap_ci(data, np.mean, n_boot=500, seed=1)
    c = stats.bootstrap_ci(data, np.mean, n_boot=500, seed=2)
    assert a == b
    assert a != c


def test_bootstrap_close_to_normal_interval_for_large_bernoulli():
    """Broken case: resampling without replacement returns a zero-width interval at 0.3."""
    r = REF["bootstrap"]
    data = np.array([1.0] * r["bernoulli_ones"] + [0.0] * (r["bernoulli_n"] - r["bernoulli_ones"]))
    lo, hi = stats.bootstrap_ci(data, np.mean, n_boot=4000, seed=1)
    nlo, nhi = r["normal_ci"]
    assert abs(lo - nlo) < r["tolerance"]
    assert abs(hi - nhi) < r["tolerance"]
    mean, se = stats.mean_se(data)
    # the code's own normal interval uses ddof=1, so it sits a hair wider than the hand value
    assert stats.normal_ci(mean, se)[0] == pytest.approx(nlo, abs=1e-4)


def test_pass_at_k_summary_unit_is_the_question():
    s = stats.pass_at_k_summary([(5, 2), (5, 5), (5, 0)], k=1, seed=1, n_boot=200)
    assert s["value"] == pytest.approx((0.4 + 1.0 + 0.0) / 3)
    assert s["n_questions"] == 3


def test_agreement_report_confusion():
    r = REF["kappa_2x2"]
    j, t = _expand_2x2(r["table"])
    rep = stats.agreement_report(j, t, seed=1, n_boot=200)
    assert rep["confusion"] == r["table"]
    lo, hi = rep["kappa"]["ci95_bootstrap"]
    assert lo <= r["kappa"] <= hi
