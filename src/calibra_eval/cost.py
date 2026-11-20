"""Cost and latency from the tokens and timings of every call."""

import tomllib
from pathlib import Path

import numpy as np


def load_prices(path) -> dict:
    """TOML like: [models."llama-3.1-8b-instant"] input_per_million = 0.05, output_per_million = 0.08"""
    if not path:
        return {}
    with open(Path(path), "rb") as f:
        return tomllib.load(f).get("models", {})


def summarize_calls(calls: list[dict], model: str, n_tasks: int, prices: dict | None = None) -> dict:
    """calls: dicts with prompt_tokens, completion_tokens, latency_ms, tokens_exact."""
    prompt = sum(c["prompt_tokens"] for c in calls)
    completion = sum(c["completion_tokens"] for c in calls)
    lat = np.array([c["latency_ms"] for c in calls], dtype=float) if calls else np.zeros(1)
    price = (prices or {}).get(model)
    cost = None
    if price:
        cost = (prompt * price["input_per_million"] + completion * price["output_per_million"]) / 1e6
    return {
        "calls": len(calls),
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "tokens_exact": bool(calls) and all(c["tokens_exact"] for c in calls),
        "tokens_per_task": (prompt + completion) / n_tasks if n_tasks else 0.0,
        "latency_ms_mean": float(lat.mean()),
        "latency_ms_p50": float(np.percentile(lat, 50)),
        "latency_ms_p95": float(np.percentile(lat, 95)),
        "cost_usd": cost,
        "cost_usd_per_task": None if cost is None or not n_tasks else cost / n_tasks,
    }
