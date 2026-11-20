"""Reports: a terminal table, Markdown (README and pull request comment) and a static HTML page.
Every number comes from a results JSON file."""

import html
import json
import os
from pathlib import Path


def load_results(folder) -> list[dict]:
    files = sorted(Path(folder).glob("*.json"))
    out = []
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        if data.get("kind") in ("eval", "judge"):
            rel = os.path.relpath(f.resolve(), Path.cwd())
            data["_file"] = Path(f if rel.startswith("..") else rel).as_posix()
            out.append(data)
    return out


def f3(x) -> str:
    return "n/a" if x is None else f"{x:.3f}"


def ci(pair) -> str:
    return "n/a" if not pair else f"[{pair[0]:.3f}, {pair[1]:.3f}]"


def val_ci(d: dict, key: str = "ci95_bootstrap") -> str:
    return f"{f3(d['value'])} {ci(d.get(key))}"


def diff_ci(d: dict) -> str:
    return f"{d['mean_diff']:+.3f} {ci(d['ci95_paired'])} (normal CI)"


def label(res: dict) -> str:
    dates = ", ".join(res["recorded_on"]) or "unknown date"
    return f"seed {res['seed']}, recorded {dates}, {res['mode']} mode"


def eval_rows(res: dict) -> tuple[list[str], list[list[str]]]:
    ks = [p["k"] for p in res["targets"][0]["pass_at_k"]]
    head = ["Target", "Model", "Pass rate (95% CI)"] + [f"pass@{k} (95% CI)" for k in ks]
    rows = []
    for t in res["targets"]:
        rows.append([t["name"], f"{t['model']} ({t['model_kind']})", val_ci(t["pass_rate"])]
                    + [val_ci(p) for p in t["pass_at_k"]])
    return head, rows


def judge_rows(res: dict) -> tuple[list[str], list[list[str]]]:
    cal, pos, verb = res["calibration"], res["position_probe"], res["verbosity_probe"]
    head = ["Measure", "Value (95% CI)"]
    rows = [
        ["Cases with ground truth", str(res["n_cases"])],
        ["Percent agreement", val_ci(cal["agreement"])],
        ["Cohen's kappa", val_ci(cal["kappa"])],
        ["Judge errors", f"{len(res['errors'])} of {res['n_cases']}"],
        ["Position: same pick after swap", val_ci(pos["consistency"])],
        ["Position: picks answer A", val_ci(pos["picks_A_rate"])],
        ["Position: accuracy gap, right answer first minus second",
         diff_ci(pos["accuracy_gap"])],
        ["Verbosity: accepts wrong answers, raw", val_ci(verb["accept_wrong_raw"])],
        ["Verbosity: accepts wrong answers, padded", val_ci(verb["accept_wrong_padded"])],
        ["Verbosity: padded minus raw, wrong answers", diff_ci(verb["wrong_padded_minus_raw"])],
    ]
    return head, rows


def md_table(head: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(head) + " |", "| " + " | ".join("---" for _ in head) + " |"]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines)


def text_table(head: list[str], rows: list[list[str]]) -> str:
    widths = [max(len(x) for x in col) for col in zip(head, *rows, strict=True)]
    fmt = "  ".join("{:<" + str(w) + "}" for w in widths)
    sep = "  ".join("-" * w for w in widths)
    return "\n".join([fmt.format(*head), sep] + [fmt.format(*r) for r in rows])


def results_markdown(results: list[dict]) -> str:
    parts = []
    for res in results:
        if res["kind"] == "eval":
            head, rows = eval_rows(res)
            parts.append(f"**{res['suite']}**: {res['n_cases']} cases, {res['samples']} samples "
                         f"each, {label(res)}. Source: `{res['_file']}`.\n\n" + md_table(head, rows))
            if res.get("paired"):
                p = res["paired"]
                parts.append(
                    f"Paired difference, {p['a']} minus {p['b']} ({p['metric']}): "
                    f"{p['mean_diff']:+.3f}, paired 95% normal CI {ci(p['ci95_paired'])}, "
                    f"unpaired 95% normal CI {ci(p['ci95_unpaired'])}, "
                    f"paired bootstrap CI {ci(p['ci95_bootstrap'])}.")
        else:
            head, rows = judge_rows(res)
            j = res["judge"]
            parts.append(f"**{res['suite']}**: judge `{j['model']}` ({j['kind']}), {label(res)}. "
                         f"Source: `{res['_file']}`.\n\n" + md_table(head, rows))
    return "\n\n".join(parts)


def cost_markdown(results: list[dict]) -> str:
    head = ["Suite", "Model", "Calls", "Tokens per task", "Exact tokens", "Latency p50 ms",
            "Cost per task (USD)"]
    rows = []
    for res in results:
        items = res["targets"] if res["kind"] == "eval" else [
            {"model": res["judge"]["model"], "cost": res["cost"]}]
        for t in items:
            c = t["cost"]
            cost = "no price set" if c["cost_usd_per_task"] is None else f"{c['cost_usd_per_task']:.6f}"
            rows.append([res["suite"], t["model"], str(c["calls"]), f"{c['tokens_per_task']:.1f}",
                         "yes" if c["tokens_exact"] else "no (word count)",
                         f"{c['latency_ms_p50']:.3f}", cost])
    return md_table(head, rows)


def errors_markdown(res: dict, limit: int = 12) -> str:
    rows = [[e["id"], e["task_type"], e["truth"], e["judge"]] for e in res["errors"][:limit]]
    return md_table(["Case", "Task", "Ground truth", "Judge said"], rows)


def terminal_report(results: list[dict]) -> str:
    out = []
    for res in results:
        out.append(f"== {res['suite']} ({label(res)})")
        head, rows = eval_rows(res) if res["kind"] == "eval" else judge_rows(res)
        out.append(text_table(head, rows))
        if res["kind"] == "eval" and res.get("paired"):
            p = res["paired"]
            out.append(f"paired {p['a']} - {p['b']}: {p['mean_diff']:+.3f} "
                       f"CI {ci(p['ci95_paired'])} (unpaired CI {ci(p['ci95_unpaired'])})")
        out.append("")
    return "\n".join(out)


def pr_comment(results: list[dict]) -> str:
    return ("## calibra-eval results\n\n" + results_markdown(results) + "\n\n"
            "Replayed from committed fixtures. Numbers from fake models are simulated.\n")


def html_page(results: list[dict]) -> str:
    def table(head, rows):
        th = "".join(f"<th>{html.escape(h)}</th>" for h in head)
        trs = "".join("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in r) + "</tr>"
                      for r in rows)
        return f"<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>"

    sections = []
    for res in results:
        head, rows = eval_rows(res) if res["kind"] == "eval" else judge_rows(res)
        body = table(head, rows)
        if res["kind"] == "eval" and res.get("paired"):
            p = res["paired"]
            body += (f"<p>Paired difference, {html.escape(p['a'])} minus {html.escape(p['b'])}: "
                     f"{p['mean_diff']:+.3f}, paired 95% CI {ci(p['ci95_paired'])}, unpaired "
                     f"95% CI {ci(p['ci95_unpaired'])}.</p>")
        if res["kind"] == "judge":
            erows = [[e["id"], e["task_type"], e["truth"], e["judge"]] for e in res["errors"]]
            body += "<h3>Every case where the judge was wrong</h3>" + table(
                ["Case", "Task", "Ground truth", "Judge said"], erows)
        sections.append(f"<section><h2>{html.escape(res['suite'])}</h2>"
                        f"<p class=meta>{html.escape(label(res))}. Source: "
                        f"<code>{html.escape(res['_file'])}</code></p>{body}</section>")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>calibra-eval results</title>
<style>
:root {{ --bg: #ffffff; --fg: #1d2330; --muted: #5b6577; --line: #d9dee7; --head: #f3f5f9; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg: #12151c; --fg: #e6e9ef; --muted: #9aa3b2; --line: #2b313d; --head: #1b2029; }}
}}
body {{ background: var(--bg); color: var(--fg); font: 15px/1.5 system-ui, sans-serif;
  max-width: 1000px; margin: 0 auto; padding: 24px 16px; }}
table {{ border-collapse: collapse; width: 100%; margin: 12px 0 24px; font-size: 14px; }}
th, td {{ border: 1px solid var(--line); padding: 6px 8px; text-align: left; }}
th {{ background: var(--head); }}
.meta, .note {{ color: var(--muted); }}
section {{ overflow-x: auto; }}
</style>
</head>
<body>
<h1>calibra-eval results</h1>
<p class=note>Every number on this page comes from the results JSON files in this repo. The
models named <code>fake:...</code> are deterministic simulators, not language models, so their
numbers are simulated.</p>
<h2>Cost per task</h2>
{table(*_cost_rows(results))}
{"".join(sections)}
</body>
</html>
"""


def _cost_rows(results):
    md = cost_markdown(results).splitlines()
    head = [c.strip() for c in md[0].strip("|").split("|")]
    rows = [[c.strip() for c in ln.strip("|").split("|")] for ln in md[2:]]
    return head, rows
