import threading
import time

from calibra_eval.cases import Case
from calibra_eval.runner import DiskCache, run_cases
from calibra_eval.targets import Output


class SlowEcho:
    id = "test:slow-echo"

    def __init__(self):
        self.calls = 0
        self.threads = set()
        self.lock = threading.Lock()

    def __call__(self, case_input, sample):
        with self.lock:
            self.calls += 1
            self.threads.add(threading.get_ident())
        time.sleep(0.05)
        if case_input == "boom":
            raise RuntimeError("target broke")
        return Output(text=case_input)


CASES = [Case(str(i), f"v{i}", {"type": "exact", "expected": f"v{i}"}) for i in range(8)]


def test_parallel_order_and_scoring():
    t = SlowEcho()
    start = time.perf_counter()
    res = run_cases(CASES, t, samples=2, workers=8)
    elapsed = time.perf_counter() - start
    assert [(r.case_id, r.sample) for r in res] == [(str(i), s) for i in range(8) for s in range(2)]
    assert all(r.passed for r in res)
    assert len(t.threads) > 1
    assert elapsed < 16 * 0.05  # faster than one worker would be


def test_disk_cache_skips_repeat_calls(tmp_path):
    t = SlowEcho()
    cache = DiskCache(tmp_path / "cache")
    run_cases(CASES, t, samples=1, workers=4, cache=cache)
    run_cases(CASES, t, samples=1, workers=4, cache=cache)
    assert t.calls == len(CASES)


def test_target_error_is_a_failed_case():
    res = run_cases([Case("x", "boom", {"type": "exact", "expected": "boom"})], SlowEcho())
    assert not res[0].passed and "target broke" in res[0].detail
