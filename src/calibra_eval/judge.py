"""Judge calibration and bias probes.

The judge grades answers whose correctness a checker already knows. Agreement and Cohen's kappa
say how far the judge can be trusted. Two probes look for the biases named in the MT-Bench paper:
swap the answer order (position bias) and pad the answer (verbosity bias).
"""

import json
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path

from .stats import agreement_report, paired_difference, proportion_summary

POINTWISE = (
    "You are grading an answer to a question.\n\nQuestion:\n{question}\n\nAnswer:\n{answer}"
    "\n\nReply with exactly one word: CORRECT or INCORRECT."
)
PAIRWISE = (
    "Two answers to the same question follow. Exactly one of them is correct.\n\n"
    "Question:\n{question}\n\nAnswer A:\n{a}\n\nAnswer B:\n{b}\n\n"
    "Which answer is correct? Reply with exactly one letter: A or B."
)
# Neutral filler. It adds length and no information.
PADDING = (
    "\n\nTo give some more context, I worked through this step by step and took care to read "
    "the question closely. I considered the problem from a few angles before I wrote the result "
    "above, and I kept the explanation focused on the task. I hope this detailed explanation is "
    "clear and useful for checking the work."
)


@dataclass(frozen=True)
class JudgeCase:
    id: str
    pair_id: str
    task_type: str
    question: str
    candidate: str
    label: bool


def load_judge_cases(path) -> list[JudgeCase]:
    cases = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            cases.append(JudgeCase(r["id"], r["pair_id"], r["task_type"], r["question"],
                                   r["candidate"], bool(r["label"])))
    ids = [c.id for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate judge case ids")
    return cases


def parse_pointwise(text: str) -> bool | None:
    t = text.upper()
    if "INCORRECT" in t:
        return False
    if "CORRECT" in t:
        return True
    return None


def parse_pairwise(text: str) -> str | None:
    m = re.search(r"\b([AB])\b", text.strip().upper())
    return m.group(1) if m else None


def _pairs(cases: list[JudgeCase]):
    groups = defaultdict(list)
    for c in cases:
        groups[c.pair_id].append(c)
    out = []
    for pid in sorted(groups):
        right = [c for c in groups[pid] if c.label]
        wrong = [c for c in groups[pid] if not c.label]
        if right and wrong:
            out.append((pid, right[0], wrong[0]))
    return out


def run_calibration(cases: list[JudgeCase], ask, seed: int = 1, workers: int = 4,
                    n_boot: int = 2000) -> tuple[dict, list[dict]]:
    """`ask(prompt) -> Output`. Returns the report and the list of call records."""
    pairs = _pairs(cases)
    prompts = [POINTWISE.format(question=c.question, answer=c.candidate) for c in cases]
    prompts += [POINTWISE.format(question=c.question, answer=c.candidate + PADDING) for c in cases]
    for _, r, w in pairs:
        prompts.append(PAIRWISE.format(question=r.question, a=r.candidate, b=w.candidate))
        prompts.append(PAIRWISE.format(question=r.question, a=w.candidate, b=r.candidate))
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        outs = list(pool.map(ask, prompts))
    calls = [asdict(o) for o in outs]

    n = len(cases)
    raw = [parse_pointwise(o.text) for o in outs[:n]]
    padded = [parse_pointwise(o.text) for o in outs[n:2 * n]]
    picks = [parse_pairwise(o.text) for o in outs[2 * n:]]
    invalid = sum(v is None for v in raw + padded) + sum(p is None for p in picks)
    # An unreadable verdict counts as "not correct": it cannot earn the judge agreement for free.
    verdict = [bool(v) for v in raw]
    verdict_pad = [bool(v) for v in padded]
    labels = [c.label for c in cases]

    by_type = {}
    for t in sorted({c.task_type for c in cases}):
        idx = [i for i, c in enumerate(cases) if c.task_type == t]
        by_type[t] = agreement_report([verdict[i] for i in idx], [labels[i] for i in idx],
                                      seed, n_boot)
    errors = [
        {"id": c.id, "task_type": c.task_type, "truth": "correct" if c.label else "wrong",
         "judge": "correct" if verdict[i] else "wrong"}
        for i, c in enumerate(cases) if verdict[i] != c.label
    ]

    right_first = [picks[2 * i] == "A" for i in range(len(pairs))]
    right_second = [picks[2 * i + 1] == "B" for i in range(len(pairs))]
    consistent = [rf == rs for rf, rs in zip(right_first, right_second, strict=True)]
    picks_a = [p == "A" for p in picks]

    wrong_idx = [i for i, c in enumerate(cases) if not c.label]
    right_idx = [i for i, c in enumerate(cases) if c.label]
    report = {
        "n_cases": n,
        "n_pairs": len(pairs),
        "invalid_verdicts": invalid,
        "calibration": agreement_report(verdict, labels, seed, n_boot),
        "by_task_type": by_type,
        "errors": errors,
        "position_probe": {
            "accuracy_right_answer_first": proportion_summary(right_first, seed, n_boot),
            "accuracy_right_answer_second": proportion_summary(right_second, seed, n_boot),
            "accuracy_gap": paired_difference(right_first, right_second, seed, n_boot),
            "consistency": proportion_summary(consistent, seed, n_boot),
            "picks_A_rate": proportion_summary(picks_a, seed, n_boot),
        },
        "verbosity_probe": {
            "pad_chars": len(PADDING),
            "accept_wrong_raw": proportion_summary([verdict[i] for i in wrong_idx], seed, n_boot),
            "accept_wrong_padded": proportion_summary([verdict_pad[i] for i in wrong_idx], seed,
                                                      n_boot),
            "wrong_padded_minus_raw": paired_difference([verdict_pad[i] for i in wrong_idx],
                                                        [verdict[i] for i in wrong_idx], seed,
                                                        n_boot),
            "accept_right_raw": proportion_summary([verdict[i] for i in right_idx], seed, n_boot),
            "accept_right_padded": proportion_summary([verdict_pad[i] for i in right_idx], seed,
                                                      n_boot),
            "right_padded_minus_raw": paired_difference([verdict_pad[i] for i in right_idx],
                                                        [verdict[i] for i in right_idx], seed,
                                                        n_boot),
        },
    }
    return report, calls
