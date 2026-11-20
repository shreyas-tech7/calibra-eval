from calibra_eval.checkers import check, extract_code, extract_json


def test_exact():
    assert check({"type": "exact", "expected": "Paris"}, " Paris\n").passed
    assert not check({"type": "exact", "expected": "Paris"}, "paris").passed
    assert check({"type": "exact", "expected": "Paris", "case_insensitive": True}, "paris").passed
    assert check({"type": "exact"}, "42", ground_truth=42).passed


def test_regex_with_capture_and_ground_truth():
    c = {"type": "regex", "pattern": r"Final answer: (-?\d+)"}
    assert check(c, "work...\nFinal answer: 12", ground_truth=12).passed
    assert not check(c, "Final answer: 13", ground_truth=12).passed
    assert not check(c, "no answer", ground_truth=12).passed


def test_json_schema_checker():
    c = {"type": "json_schema", "schema": {"type": "object", "required": ["a"]}}
    assert check(c, '```json\n{"a": 1}\n```').passed
    assert check(c, 'Here: {"a": 1} done').passed
    assert not check(c, '{"b": 1}').passed
    assert not check(c, "not json").passed
    assert not check(c, '{"a": 2}', ground_truth={"a": 1}).passed


def test_unittest_checker_pass_fail_and_timeout():
    """Broken case: running tests in-process would let `while True` hang the whole run."""
    tests = "assert add(2, 3) == 5"
    good = "```python\ndef add(a, b):\n    return a + b\n```"
    bad = "def add(a, b):\n    return a - b"
    assert check({"type": "unittest", "tests": tests}, good).passed
    assert not check({"type": "unittest", "tests": tests}, bad).passed
    hang = "def add(a, b):\n    while True:\n        pass"
    r = check({"type": "unittest", "tests": tests, "timeout_s": 1}, hang)
    assert not r.passed and "timeout" in r.detail


def test_extract_helpers():
    assert extract_code("x\n```py\nprint(1)\n```") == "print(1)\n"
    assert extract_code("plain") == "plain"
    assert extract_json('{"k": [1]}') == {"k": [1]}
