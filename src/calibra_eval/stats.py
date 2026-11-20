"""Statistics for evals. Follows Evan Miller, "Adding Error Bars to Evals" (arXiv 2411.00640).

The unit of analysis is the question. When a question has several samples, average them first,
then take the standard error over questions.
"""

import math

import numpy as np

Z95 = 1.959963984540054


def mean_se(values) -> tuple[float, float | None]:
    """Mean and standard error with the sample standard deviation (ddof=1).
    The standard error is None when there are fewer than 2 values."""
    x = np.asarray(values, dtype=float)
    if x.size == 0:
        raise ValueError("no values")
    if x.size < 2:
        return float(x.mean()), None
    return float(x.mean()), float(x.std(ddof=1) / math.sqrt(x.size))


def normal_ci(mean: float, se: float | None) -> list[float] | None:
    if se is None:
        return None
    return [mean - Z95 * se, mean + Z95 * se]


def bootstrap_ci(data, statistic, n_boot: int = 2000, seed: int = 1, alpha: float = 0.05):
    """Percentile bootstrap. `data` is a sequence of rows. Rows are resampled with replacement."""
    rows = np.asarray(data)
    n = len(rows)
    if n == 0:
        raise ValueError("no data")
    rng = np.random.default_rng(seed)
    stats = np.empty(n_boot)
    for i in range(n_boot):
        stats[i] = statistic(rows[rng.integers(0, n, n)])
    lo, hi = np.quantile(stats, [alpha / 2, 1 - alpha / 2])
    return [float(lo), float(hi)]


def pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased pass@k from Chen et al. 2021: 1 - C(n-c, k) / C(n, k)."""
    if not 0 <= c <= n or not 1 <= k <= n:
        raise ValueError(f"need 0 <= c <= n and 1 <= k <= n, got n={n} c={c} k={k}")
    if n - c < k:
        return 1.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def pass_at_k_summary(counts, k: int, seed: int = 1, n_boot: int = 2000) -> dict:
    """counts: list of (n, c) per question. Returns the mean pass@k over questions with intervals."""
    per_q = np.array([pass_at_k(n, c, k) for n, c in counts])
    mean, se = mean_se(per_q)
    return {
        "k": k,
        "value": mean,
        "se": se,
        "ci95_normal": normal_ci(mean, se),
        "ci95_bootstrap": bootstrap_ci(per_q, np.mean, n_boot, seed),
        "n_questions": len(per_q),
    }


def paired_difference(a, b, seed: int = 1, n_boot: int = 2000) -> dict:
    """Mean of a - b over the same questions. The paired SE uses the per-question differences.
    The unpaired SE ignores the pairing, for comparison."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.shape != b.shape:
        raise ValueError("a and b must score the same questions")
    d = a - b
    mean, se_paired = mean_se(d)
    _, se_a = mean_se(a)
    _, se_b = mean_se(b)
    se_unpaired = None if se_a is None else math.sqrt(se_a**2 + se_b**2)
    corr = None
    if a.std() > 0 and b.std() > 0:
        corr = float(np.corrcoef(a, b)[0, 1])
    return {
        "mean_diff": mean,
        "se_paired": se_paired,
        "se_unpaired": se_unpaired,
        "ci95_paired": normal_ci(mean, se_paired),
        "ci95_unpaired": normal_ci(mean, se_unpaired),
        "ci95_bootstrap": bootstrap_ci(d, np.mean, n_boot, seed),
        "correlation": corr,
        "n_questions": int(d.size),
    }


def percent_agreement(x, y) -> float:
    x, y = np.asarray(x), np.asarray(y)
    return float(np.mean(x == y))


def cohen_kappa(x, y) -> float:
    """Cohen's kappa: (po - pe) / (1 - pe). When pe is 1, both raters used one label only:
    kappa is 1 if they agree everywhere, else 0."""
    x, y = np.asarray(x), np.asarray(y)
    po = float(np.mean(x == y))
    labels = np.union1d(x, y)
    pe = float(sum(np.mean(x == lab) * np.mean(y == lab) for lab in labels))
    if pe >= 1.0:
        return 1.0 if po == 1.0 else 0.0
    return (po - pe) / (1.0 - pe)


def agreement_report(judge, truth, seed: int = 1, n_boot: int = 2000) -> dict:
    """Agreement and kappa between judge verdicts and ground truth, each with a bootstrap CI."""
    j = np.asarray(judge, dtype=int)
    t = np.asarray(truth, dtype=int)
    pairs = np.stack([j, t], axis=1)
    return {
        "n": int(len(j)),
        "agreement": {
            "value": percent_agreement(j, t),
            "ci95_bootstrap": bootstrap_ci(pairs, lambda r: percent_agreement(r[:, 0], r[:, 1]),
                                           n_boot, seed),
        },
        "kappa": {
            "value": cohen_kappa(j, t),
            "ci95_bootstrap": bootstrap_ci(pairs, lambda r: cohen_kappa(r[:, 0], r[:, 1]),
                                           n_boot, seed),
        },
        "confusion": {
            "judge_yes_truth_yes": int(np.sum((j == 1) & (t == 1))),
            "judge_yes_truth_no": int(np.sum((j == 1) & (t == 0))),
            "judge_no_truth_yes": int(np.sum((j == 0) & (t == 1))),
            "judge_no_truth_no": int(np.sum((j == 0) & (t == 0))),
        },
    }


def proportion_summary(values, seed: int = 1, n_boot: int = 2000) -> dict:
    mean, se = mean_se(values)
    return {
        "value": mean,
        "se": se,
        "ci95_normal": normal_ci(mean, se),
        "ci95_bootstrap": bootstrap_ci(np.asarray(values, dtype=float), np.mean, n_boot, seed),
        "n": len(values),
    }
