"""Run a target over cases with parallel workers and a disk cache."""

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path

from .canon import canonical_json, sha256_hex
from .cases import Case
from .checkers import check
from .fixtures import MissingFixture
from .targets import ModelTarget, Output


@dataclass(frozen=True)
class SampleResult:
    case_id: str
    sample: int
    passed: bool
    detail: str
    output: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    tokens_exact: bool


class DiskCache:
    """One JSON file per call, keyed by target id, input and sample number."""

    def __init__(self, folder):
        self.folder = Path(folder)

    def _path(self, target_id: str, case_input, sample: int) -> Path:
        key = sha256_hex(canonical_json({"target": target_id, "input": case_input, "sample": sample}))
        return self.folder / f"{key}.json"

    def get(self, target_id, case_input, sample):
        p = self._path(target_id, case_input, sample)
        return Output(**json.loads(p.read_text(encoding="utf-8"))) if p.exists() else None

    def put(self, target_id, case_input, sample, out: Output) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        self._path(target_id, case_input, sample).write_text(canonical_json(asdict(out)),
                                                             encoding="utf-8")


def _call(target, case: Case, sample: int, cache: DiskCache | None) -> Output:
    # Model targets already cache through fixtures, so the disk cache skips them.
    use_cache = cache is not None and not isinstance(target, ModelTarget)
    if use_cache:
        hit = cache.get(target.id, case.input, sample)
        if hit is not None:
            return hit
    out = target(case.input, sample)
    if use_cache:
        cache.put(target.id, case.input, sample, out)
    return out


def run_cases(cases: list[Case], target, samples: int = 1, workers: int = 4,
              cache: DiskCache | None = None) -> list[SampleResult]:
    """Results come back in case order, then sample order, whatever the worker count."""
    jobs = [(c, s) for c in cases for s in range(samples)]

    def one(job) -> SampleResult:
        case, sample = job
        try:
            out = _call(target, case, sample, cache)
        except MissingFixture:
            raise
        except Exception as e:  # a crashing target is a failed case, not a crashed run
            return SampleResult(case.id, sample, False, f"target error: {e}", "", 0, 0, 0.0, False)
        res = check(case.checker, out.text, case.ground_truth)
        return SampleResult(case.id, sample, res.passed, res.detail, out.text, out.prompt_tokens,
                            out.completion_tokens, out.latency_ms, out.tokens_exact)

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        return list(pool.map(one, jobs))
