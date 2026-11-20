"""The README tables must match the result files exactly. Nobody types the numbers."""

import os
import re
from pathlib import Path

from calibra_eval.readme import render
from calibra_eval.report import load_results

ROOT = Path(__file__).resolve().parent.parent


def test_readme_tables_match_results():
    """Broken case: a number typed into the README by hand makes this fail."""
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        readme = Path("README.md").read_text()
        assert render(readme, load_results("results"), load_results("results/seed2")) == readme
    finally:
        os.chdir(cwd)


def test_every_number_in_results_block_appears_in_a_results_file():
    readme = (ROOT / "README.md").read_text()
    block = readme.split("<!-- calibra:results:start -->")[1].split("<!-- calibra:results:end -->")[0]
    blob = "".join(p.read_text() for p in (ROOT / "results").glob("*.json"))
    known = [float(x) for x in re.findall(r"-?\d+\.\d+", blob)] + [1.0, 0.0]
    for num in set(re.findall(r"\d\.\d{3}", block)):
        value = float(num)
        assert any(abs(x - value) <= 0.0005 + 1e-9 for x in known), num
