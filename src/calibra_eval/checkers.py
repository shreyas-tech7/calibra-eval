"""Code checkers: exact match, regex, JSON schema and a unit test run."""

import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .schema import validate

UNITTEST_TIMEOUT_S = 10


def clean_env() -> dict:
    """Model-written code gets PATH and nothing else, so it never sees API keys.

    This is not a sandbox. The code can still read files and use the network.
    """
    return {"PATH": os.environ.get("PATH", "")}


@dataclass(frozen=True)
class CheckResult:
    passed: bool
    detail: str = ""


def extract_code(text: str) -> str:
    """Take the first fenced code block, or the whole text when there is none."""
    m = re.search(r"```(?:python|py)?\s*\n(.*?)```", text, re.S)
    return m.group(1) if m else text


def extract_json(text: str):
    """Parse JSON from a fenced block, the whole text, or the first {...} span."""
    m = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.S)
    candidates = [m.group(1)] if m else []
    candidates.append(text)
    brace = re.search(r"\{.*\}", text, re.S)
    if brace:
        candidates.append(brace.group(0))
    for c in candidates:
        try:
            return json.loads(c)
        except json.JSONDecodeError:
            continue
    raise ValueError("no JSON found in output")


def check_exact(checker: dict, output: str, ground_truth=None) -> CheckResult:
    expected = checker.get("expected", ground_truth)
    got = output.strip()
    want = str(expected).strip()
    if checker.get("case_insensitive"):
        got, want = got.lower(), want.lower()
    return CheckResult(got == want, f"expected {want!r}, got {got!r}")


def check_regex(checker: dict, output: str, ground_truth=None) -> CheckResult:
    pattern = checker["pattern"]
    m = re.search(pattern, output, re.S)
    if not m:
        return CheckResult(False, f"no match for {pattern!r}")
    if ground_truth is not None and m.groups():
        ok = m.group(1).strip() == str(ground_truth).strip()
        return CheckResult(ok, f"captured {m.group(1)!r}, expected {ground_truth!r}")
    return CheckResult(True, "matched")


def check_json_schema(checker: dict, output: str, ground_truth=None) -> CheckResult:
    try:
        data = extract_json(output)
    except ValueError as e:
        return CheckResult(False, str(e))
    errors = validate(data, checker["schema"])
    if errors:
        return CheckResult(False, "; ".join(errors))
    if ground_truth is not None and data != ground_truth:
        return CheckResult(False, f"valid schema but value differs from ground truth: {data!r}")
    return CheckResult(True, "valid")


def check_unittest(checker: dict, output: str, ground_truth=None) -> CheckResult:
    """Run the extracted code plus the checker's test code in a fresh, isolated interpreter."""
    code = extract_code(output)
    tests = checker["tests"]
    timeout = checker.get("timeout_s", UNITTEST_TIMEOUT_S)
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "run_test.py"
        script.write_text(code + "\n\n" + tests + "\n", encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, "-I", str(script)],
                cwd=tmp,
                env=clean_env(),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return CheckResult(False, f"timeout after {timeout}s")
    if proc.returncode == 0:
        return CheckResult(True, "tests passed")
    tail = (proc.stderr or proc.stdout).strip().splitlines()[-1:] or ["failed"]
    return CheckResult(False, tail[0][:200])


CHECKERS = {
    "exact": check_exact,
    "regex": check_regex,
    "json_schema": check_json_schema,
    "unittest": check_unittest,
}


def check(checker: dict, output: str, ground_truth=None) -> CheckResult:
    return CHECKERS[checker["type"]](checker, output, ground_truth)
