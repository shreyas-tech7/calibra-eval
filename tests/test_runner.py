import json
import threading
import time

import pytest

from calibra_eval.adapter import ProviderError
from calibra_eval.cases import Case
from calibra_eval.runner import DiskCache, run_cases
from calibra_eval.suite import run_eval_suite
from calibra_eval.targets import FunctionTarget, Output, ShellTarget


class SlowEcho:
    id = "test:slow-echo"
    cache_key = "test:slow-echo"

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


def test_cache_misses_after_the_function_file_changes(tmp_path):
    """Broken case: a cache keyed only by the function name serves the old output after an edit."""
    src = tmp_path / "t.py"
    src.write_text("def f(x):\n    return 'old value'\n")
    cache = DiskCache(tmp_path / "cache")
    case = [Case("a", "in", {"type": "exact", "expected": "new"})]
    assert not run_cases(case, FunctionTarget({"function": "t.py:f"}, tmp_path), cache=cache)[0].passed
    src.write_text("def f(x):\n    return 'new'\n")
    assert run_cases(case, FunctionTarget({"function": "t.py:f"}, tmp_path), cache=cache)[0].passed


def test_shell_targets_are_not_cached(tmp_path):
    t = ShellTarget({"command": ["cat"]}, tmp_path)
    assert t.cache_key is None


def test_provider_error_stops_the_run():
    class Down:
        id = "test:down"

        def __call__(self, case_input, sample):
            raise ProviderError("HTTP 503")

    with pytest.raises(ProviderError):
        run_cases(CASES, Down())


def test_record_run_keeps_fixtures_when_the_provider_fails(tmp_path, monkeypatch):
    """Broken case: saving only at the end loses every call recorded before the failure."""
    from calibra_eval import fake

    (tmp_path / "cases.jsonl").write_text("".join(
        json.dumps({"id": str(i), "input": f"q{i}", "checker": {"type": "exact", "expected": "x"}})
        + "\n" for i in range(4)))
    real_call = fake.FakeModel.__call__
    seen = []

    def flaky(self, request):
        seen.append(1)
        if len(seen) > 2:
            raise ProviderError("HTTP 503")
        return real_call(self, request)

    monkeypatch.setattr(fake.FakeModel, "__call__", flaky)
    cfg = {"name": "s", "cases": "cases.jsonl", "fixtures": "fx.jsonl", "cache": False,
           "targets": [{"name": "m", "type": "model", "model": "fake:coder-weak"}]}
    with pytest.raises(ProviderError):
        run_eval_suite(cfg, tmp_path, "record", 1, 1, {})
    assert len((tmp_path / "fx.jsonl").read_text().splitlines()) == 2
