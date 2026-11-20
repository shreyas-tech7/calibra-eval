"""Write the README tables from the result files. Nobody types the numbers."""

from pathlib import Path

from .report import cost_markdown, errors_markdown, load_results, results_markdown


def _marker(name: str, end: bool = False) -> str:
    return f"<!-- calibra:{name}:{'end' if end else 'start'} -->"


def blocks(results: list[dict], seed2: list[dict]) -> dict[str, str]:
    judge = [r for r in results if r["kind"] == "judge"]
    return {
        "results": results_markdown(results),
        "cost": cost_markdown(results),
        "judge-errors": errors_markdown(judge[0]) if judge else "No judge results yet.",
        "seed2": results_markdown(seed2) if seed2 else "No seed 2 rerun yet.",
    }


def render(readme_text: str, results: list[dict], seed2: list[dict] | None = None) -> str:
    out = readme_text
    for name, body in blocks(results, seed2 or []).items():
        start, end = _marker(name), _marker(name, True)
        if start not in out or end not in out:
            raise ValueError(f"README is missing the {start} ... {end} markers")
        head, rest = out.split(start, 1)
        _, tail = rest.split(end, 1)
        out = f"{head}{start}\n{body}\n{end}{tail}"
    return out


def update(readme_path="README.md", results_dir="results", check: bool = False) -> bool:
    """Return True when the README already matches. With check=False, rewrite it."""
    path = Path(readme_path)
    old = path.read_text(encoding="utf-8")
    seed2_dir = Path(results_dir) / "seed2"
    seed2 = load_results(seed2_dir) if seed2_dir.is_dir() else []
    new = render(old, load_results(results_dir), seed2)
    if not check and new != old:
        path.write_text(new, encoding="utf-8")
    return new == old
