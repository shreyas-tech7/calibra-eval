"""Render the pull request comment body to a file. No GitHub needed."""

from pathlib import Path

from calibra_eval.cli import main

ROOT = Path(__file__).resolve().parent.parent


def test_pr_comment_renders_to_file(tmp_path):
    out = tmp_path / "comment.md"
    assert main(["pr-comment", "--results", str(ROOT / "results"), "--out", str(out)]) == 0
    body = out.read_text()
    assert body.startswith("## calibra-eval results")
    assert "Cohen's kappa" in body and "| strong |" in body
    assert "simulated" in body


def test_workflow_uses_the_same_command():
    wf = (ROOT / ".github/workflows/eval-comment.yml").read_text()
    assert "calibra pr-comment" in wf
    action = (ROOT / "action.yml").read_text()
    assert "calibra pr-comment" in action


def test_cli_missing_fixture_is_a_clean_error(tmp_path, capsys):
    import shutil

    suite = tmp_path / "je"
    shutil.copytree(ROOT / "examples/json_extract", suite, ignore=shutil.ignore_patterns(".calibra_cache"))
    (suite / "fixtures.jsonl").write_text("")
    assert main(["run", "--out", str(tmp_path / "out"), str(suite / "suite.toml")]) == 2
    assert "Run with --record" in capsys.readouterr().err
