"""Load a TOML suite and run it: cases, target, checkers, optional judge pass, statistics."""

import json
import tomllib
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from .cases import load_cases
from .cost import load_prices, summarize_calls
from .fixtures import FixtureStore
from .judge import load_judge_cases, run_calibration
from .runner import DiskCache, run_cases
from .stats import paired_difference, pass_at_k_summary, proportion_summary
from .targets import make_target


def load_suite(path) -> tuple[dict, Path]:
    path = Path(path)
    with open(path, "rb") as f:
        return tomllib.load(f), path.parent


def _round(obj, places: int = 6):
    """Round floats so the JSON stays short and stable."""
    if isinstance(obj, float):
        return round(obj, places)
    if isinstance(obj, dict):
        return {k: _round(v, places) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round(v, places) for v in obj]
    return obj


def _model_kind(model: str) -> str:
    return "fake" if model.startswith("fake:") else "real"


def run_eval_suite(cfg: dict, base: Path, mode: str, seed: int, workers: int,
                   prices: dict) -> dict:
    cases = load_cases(base / cfg["cases"])
    samples = int(cfg.get("samples", 1))
    ks = [k for k in cfg.get("k", [1]) if k <= samples]
    n_boot = int(cfg.get("n_boot", 2000))
    store = FixtureStore(base / cfg.get("fixtures", "fixtures.jsonl"))
    cache = DiskCache(base / ".calibra_cache") if cfg.get("cache", True) else None
    targets_out, per_question = [], {}
    case_rows = defaultdict(dict)
    for spec in cfg["targets"]:
        target = make_target(spec, base, store, mode, seed, cfg.get("recorded_on", ""))
        results = run_cases(cases, target, samples, workers, cache)
        counts = defaultdict(int)
        for r in results:
            counts[r.case_id] += int(r.passed)
        per_q = [counts[c.id] / samples for c in cases]
        per_question[spec["name"]] = per_q
        for c in cases:
            case_rows[c.id][spec["name"]] = f"{counts[c.id]}/{samples}"
        model = spec.get("model", target.id)
        calls = [asdict(r) for r in results]
        targets_out.append({
            "name": spec["name"],
            "model": model,
            "model_kind": _model_kind(model) if spec.get("type", "model") == "model" else "code",
            "pass_rate": proportion_summary(per_q, seed, n_boot),
            "pass_at_k": [pass_at_k_summary([(samples, counts[c.id]) for c in cases], k, seed,
                                            n_boot) for k in ks],
            "cost": summarize_calls(calls, model, len(cases) * samples, prices),
        })
    paired = None
    names = [t["name"] for t in targets_out]
    if len(names) >= 2:
        a, b = names[0], names[1]
        paired = {"a": a, "b": b, "metric": "per-question pass rate",
                  **paired_difference(per_question[a], per_question[b], seed, n_boot)}
    if mode == "record" and store.dirty:
        store.save()
    return {
        "suite": cfg["name"],
        "kind": "eval",
        "description": cfg.get("description", ""),
        "mode": mode,
        "seed": seed,
        "samples": samples,
        "n_cases": len(cases),
        "recorded_on": store.dates(),
        "targets": targets_out,
        "paired": paired,
        "cases": [{"id": cid, **row} for cid, row in case_rows.items()],
    }


def run_judge_suite(cfg: dict, base: Path, mode: str, seed: int, workers: int,
                    prices: dict) -> dict:
    cases = load_judge_cases(base / cfg["cases"])
    store = FixtureStore(base / cfg.get("fixtures", "fixtures.jsonl"))
    spec = dict(cfg["judge"])
    spec.setdefault("temperature", 0.0)
    spec.setdefault("max_tokens", 8)
    judge = make_target(spec, base, store, mode, seed, cfg.get("recorded_on", ""))
    report, calls = run_calibration(cases, lambda p: judge(p, 0), seed, workers,
                                    int(cfg.get("n_boot", 2000)))
    if mode == "record" and store.dirty:
        store.save()
    model = spec["model"]
    return {
        "suite": cfg["name"],
        "kind": "judge",
        "description": cfg.get("description", ""),
        "mode": mode,
        "seed": seed,
        "recorded_on": store.dates(),
        "judge": {"name": spec["name"], "model": model, "kind": _model_kind(model)},
        **report,
        "cost": summarize_calls(calls, model, len(cases), prices),
    }


def run_suite(path, mode: str = "replay", seed: int | None = None, workers: int | None = None,
              prices_path=None) -> dict:
    cfg, base = load_suite(path)
    seed = int(cfg.get("seed", 1) if seed is None else seed)
    workers = int(cfg.get("workers", 4) if workers is None else workers)
    prices = load_prices(prices_path or (base / cfg["prices"] if cfg.get("prices") else None))
    runner = run_judge_suite if cfg.get("kind") == "judge" else run_eval_suite
    return _round(runner(cfg, base, mode, seed, workers, prices))


def write_json(result: dict, path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
