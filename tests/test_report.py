import json
from pathlib import Path

from calibra_eval.report import (
    cost_markdown,
    html_page,
    load_results,
    md_table,
    results_markdown,
    terminal_report,
    text_table,
)

ROOT = Path(__file__).resolve().parent.parent


def _results():
    return load_results(ROOT / "results")


def test_load_results_finds_the_three_suites():
    names = sorted(r["suite"] for r in _results())
    assert names == ["code_tasks", "json_extract", "judge_calibration"]


def test_tables_carry_numbers_from_the_json():
    res = {r["suite"]: r for r in _results()}
    md = results_markdown(list(res.values()))
    kappa = res["judge_calibration"]["calibration"]["kappa"]["value"]
    assert f"{kappa:.3f}" in md
    strong = res["code_tasks"]["targets"][0]["pass_rate"]["value"]
    assert f"| strong | fake:coder-strong (fake) | {strong:.3f}" in md
    assert "seed 1" in md and "2026-11-20" in md


def test_terminal_and_text_table():
    out = terminal_report(_results())
    assert "== judge_calibration" in out and "Cohen's kappa" in out
    t = text_table(["a", "bb"], [["1", "2"]])
    assert t.splitlines()[0] == "a  bb"
    assert md_table(["x"], [["1"]]) == "| x |\n| --- |\n| 1 |"


def test_html_page_is_static_and_lists_every_judge_error(tmp_path):
    results = _results()
    page = html_page(results)
    assert page.startswith("<!doctype html>")
    assert "<script" not in page and "http" not in page.split("<body>")[1]
    judge = [r for r in results if r["kind"] == "judge"][0]
    for e in judge["errors"]:
        assert f"<td>{e['id']}</td>" in page
    (tmp_path / "index.html").write_text(page)


def test_cost_table_says_when_tokens_are_word_counts():
    md = cost_markdown(_results())
    assert "no (word count)" in md and "no price set" in md


def test_committed_html_page_matches_results():
    page = (ROOT / "docs" / "index.html").read_text()
    assert page == html_page(_results())


def test_results_json_is_sorted_and_ends_with_newline():
    for f in (ROOT / "results").glob("*.json"):
        text = f.read_text()
        assert text.endswith("\n")
        assert text == json.dumps(json.loads(text), indent=2, sort_keys=True) + "\n"
