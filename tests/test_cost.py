import pytest

from calibra_eval.cost import load_prices, summarize_calls


def test_summary_without_prices():
    calls = [{"prompt_tokens": 10, "completion_tokens": 5, "latency_ms": 100.0, "tokens_exact": True},
             {"prompt_tokens": 20, "completion_tokens": 5, "latency_ms": 300.0, "tokens_exact": True}]
    s = summarize_calls(calls, "m", n_tasks=2)
    assert s["prompt_tokens"] == 30 and s["completion_tokens"] == 10
    assert s["tokens_per_task"] == 20.0
    assert s["latency_ms_mean"] == 200.0 and s["latency_ms_p50"] == 200.0
    assert s["cost_usd"] is None and s["tokens_exact"]


def test_summary_with_price_table(tmp_path):
    p = tmp_path / "prices.toml"
    p.write_text('[models."m"]\ninput_per_million = 1.0\noutput_per_million = 2.0\n')
    prices = load_prices(p)
    calls = [{"prompt_tokens": 1_000_000, "completion_tokens": 500_000, "latency_ms": 1.0,
              "tokens_exact": False}]
    s = summarize_calls(calls, "m", n_tasks=4, prices=prices)
    assert s["cost_usd"] == pytest.approx(2.0)
    assert s["cost_usd_per_task"] == pytest.approx(0.5)
    assert not s["tokens_exact"]
    assert load_prices(None) == {}
