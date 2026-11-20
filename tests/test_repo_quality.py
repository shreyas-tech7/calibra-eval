"""Part 1 section 9 quality bar, checked by code."""

import re
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

README_PARTS = ["**Status:**", "## The problem", "```mermaid", "## Results", "## Cost per task",
                "## Run it in 10 minutes", "## Limits", "## Glossary", "## Related work",
                "## How this was built"]

REQUIRED = ["LICENSE", "CHANGELOG.md", "CONTRIBUTING.md", ".github/ISSUE_TEMPLATE/bug_report.md",
            ".github/ISSUE_TEMPLATE/feature_request.md", ".github/workflows/ci.yml", "action.yml",
            "docs/GITHUB_ABOUT.md", "docs/social-preview.png", "docs/index.html", "docs/DEMO.md",
            "docs/WALKTHROUGH.md", "docs/INTERVIEW_QA.md", "docs/HUMAN_STEPS.md",
            "docs/handoff/COWORK_PROMPT.md", "docs/build/BUILD_PROMPT.md", ".env.example",
            ".pre-commit-config.yaml"]


def test_readme_parts_in_order():
    text = (ROOT / "README.md").read_text()
    positions = [text.find(p) for p in README_PARTS]
    assert all(p >= 0 for p in positions), dict(zip(README_PARTS, positions, strict=True))
    assert positions == sorted(positions)
    assert "actions/workflows/ci.yml/badge.svg" in text
    assert "docs/build/BUILD_PROMPT.md" in text and "not done yet" in text


def test_required_files_exist():
    missing = [f for f in REQUIRED if not (ROOT / f).is_file()]
    assert not missing


def test_license_is_mit_for_shreyas():
    text = (ROOT / "LICENSE").read_text()
    assert text.startswith("MIT License") and "Copyright (c) 2026 Shreyas" in text


def test_social_preview_size():
    data = (ROOT / "docs/social-preview.png").read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    w, h = struct.unpack(">II", data[16:24])
    assert (w, h) == (1280, 640)


def _prose(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", "", text)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return "\n".join(ln for ln in text.splitlines() if not ln.lstrip().startswith("|"))


def test_writing_rules_in_readme_and_docs():
    """No em dashes, no dashes as punctuation, no semicolons in prose, no listed filler words."""
    files = [ROOT / "README.md", ROOT / "CONTRIBUTING.md"] + sorted((ROOT / "docs").glob("*.md"))
    banned = ["it is important to note", "testament", "pivotal", "seamless", "delve"]
    for f in files:
        prose = _prose(f.read_text())
        assert "—" not in prose and "–" not in prose, f"dash in {f.name}"
        assert " - " not in prose.replace("\n- ", "\n"), f"dash as punctuation in {f.name}"
        assert ";" not in prose, f"semicolon in {f.name}"
        low = prose.lower()
        assert not [w for w in banned if w in low], f.name


def test_link_checker_passes():
    proc = subprocess.run([sys.executable, str(ROOT / "scripts/check_links.py")], capture_output=True,
                          text=True, timeout=60)
    assert proc.returncode == 0, proc.stdout[-2000:]
