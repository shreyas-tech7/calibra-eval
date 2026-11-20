"""Write the three example suites' cases and fake answer banks. Synthetic data only.

Run: .venv/bin/python scripts/build_examples.py
The judge cases get their labels from the checkers, so ground truth is code, not opinion.
Run this once, commit the cases, and only then record the judge fixtures.
"""

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from calibra_eval.checkers import check  # noqa: E402

SEED = 1

# name, signature, description, visible asserts, hidden asserts, good code, bad code that fails
# a visible test, bad code that passes the visible tests and fails a hidden one.
CODE_TASKS = [
    ("add", "add(a, b)", "returns the sum of a and b",
     ["add(2, 3) == 5", "add(10, 4) == 14"], ["add(-2, 3) == 1", "add(0, 0) == 0"],
     "def add(a, b):\n    return a + b",
     "def add(a, b):\n    return a - b",
     "def add(a, b):\n    return a + b if a >= 0 else b"),
    ("is_even", "is_even(n)", "returns True when the integer n is even",
     ["is_even(4) is True", "is_even(7) is False"], ["is_even(0) is True", "is_even(-2) is True"],
     "def is_even(n):\n    return n % 2 == 0",
     "def is_even(n):\n    return n % 2 == 1",
     "def is_even(n):\n    return n > 0 and n % 2 == 0"),
    ("reverse_words", "reverse_words(s)", "returns the words of s in reverse order, joined by one space",
     ["reverse_words('a b c') == 'c b a'", "reverse_words('hi') == 'hi'"],
     ["reverse_words('one  two') == 'two one'", "reverse_words(' x y ') == 'y x'"],
     "def reverse_words(s):\n    return ' '.join(s.split()[::-1])",
     "def reverse_words(s):\n    return s[::-1]",
     "def reverse_words(s):\n    return ' '.join(s.split(' ')[::-1])"),
    ("fizzbuzz", "fizzbuzz(n)",
     "returns 'Fizz' for multiples of 3, 'Buzz' for multiples of 5, 'FizzBuzz' for multiples of both, "
     "else str(n)",
     ["fizzbuzz(3) == 'Fizz'", "fizzbuzz(5) == 'Buzz'"],
     ["fizzbuzz(15) == 'FizzBuzz'", "fizzbuzz(7) == '7'"],
     "def fizzbuzz(n):\n    if n % 15 == 0:\n        return 'FizzBuzz'\n    if n % 3 == 0:\n"
     "        return 'Fizz'\n    if n % 5 == 0:\n        return 'Buzz'\n    return str(n)",
     "def fizzbuzz(n):\n    return 'Fizz' if n % 5 == 0 else 'Buzz'",
     "def fizzbuzz(n):\n    if n % 3 == 0:\n        return 'Fizz'\n    if n % 5 == 0:\n"
     "        return 'Buzz'\n    if n % 15 == 0:\n        return 'FizzBuzz'\n    return str(n)"),
    ("max_of", "max_of(xs)", "returns the largest number in the non-empty list xs",
     ["max_of([1, 5, 3]) == 5", "max_of([2]) == 2"], ["max_of([-4, -2, -9]) == -2"],
     "def max_of(xs):\n    return max(xs)",
     "def max_of(xs):\n    return min(xs)",
     "def max_of(xs):\n    best = 0\n    for x in xs:\n        if x > best:\n            best = x\n"
     "    return best"),
    ("count_vowels", "count_vowels(s)", "returns how many letters of s are vowels (a, e, i, o, u, any case)",
     ["count_vowels('hello') == 2", "count_vowels('sky') == 0"], ["count_vowels('AEIOU') == 5"],
     "def count_vowels(s):\n    return sum(c in 'aeiouAEIOU' for c in s)",
     "def count_vowels(s):\n    return sum(c not in 'aeiou' for c in s)",
     "def count_vowels(s):\n    return sum(c in 'aeiou' for c in s)"),
    ("factorial", "factorial(n)", "returns n! for an integer n >= 0",
     ["factorial(0) == 1", "factorial(1) == 1"], ["factorial(5) == 120", "factorial(3) == 6"],
     "def factorial(n):\n    out = 1\n    for i in range(2, n + 1):\n        out *= i\n    return out",
     "def factorial(n):\n    return n * (n - 1)",
     "def factorial(n):\n    out = 1\n    for i in range(1, n):\n        out *= i\n    return out"),
    ("is_palindrome", "is_palindrome(s)",
     "returns True when s reads the same both ways, ignoring case and anything that is not a letter "
     "or digit",
     ["is_palindrome('racecar') is True", "is_palindrome('hello') is False"],
     ["is_palindrome('A man, a plan, a canal: Panama') is True"],
     "def is_palindrome(s):\n    t = [c.lower() for c in s if c.isalnum()]\n    return t == t[::-1]",
     "def is_palindrome(s):\n    return True",
     "def is_palindrome(s):\n    return s == s[::-1]"),
    ("flatten", "flatten(xs)", "flattens a list of lists by one level",
     ["flatten([[1], [2]]) == [1, 2]", "flatten([]) == []"], ["flatten([[1, 2], [3]]) == [1, 2, 3]"],
     "def flatten(xs):\n    return [y for x in xs for y in x]",
     "def flatten(xs):\n    return xs",
     "def flatten(xs):\n    return [x[0] for x in xs]"),
    ("dedupe", "dedupe(xs)", "removes repeated items from xs and keeps the first-seen order",
     ["dedupe([1, 1, 2]) == [1, 2]", "dedupe([3, 3]) == [3]"], ["dedupe([1, 2, 1]) == [1, 2]"],
     "def dedupe(xs):\n    return list(dict.fromkeys(xs))",
     "def dedupe(xs):\n    return xs",
     "def dedupe(xs):\n    out = []\n    for x in xs:\n        if x not in out[-1:]:\n"
     "            out.append(x)\n    return out"),
    ("clamp", "clamp(x, lo, hi)", "returns x limited to the range lo to hi",
     ["clamp(5, 0, 10) == 5", "clamp(-3, 0, 10) == 0"], ["clamp(15, 0, 10) == 10"],
     "def clamp(x, lo, hi):\n    return max(lo, min(x, hi))",
     "def clamp(x, lo, hi):\n    return min(lo, max(x, hi))",
     "def clamp(x, lo, hi):\n    if x < lo:\n        return lo\n    return x"),
    ("word_count", "word_count(s)",
     "returns a dict from each lowercased word in s to how often it appears",
     ["word_count('a b a') == {'a': 2, 'b': 1}", "word_count('') == {}"],
     ["word_count('The the') == {'the': 2}"],
     "def word_count(s):\n    out = {}\n    for w in s.lower().split():\n        out[w] = out.get(w, 0) + 1\n"
     "    return out",
     "def word_count(s):\n    return len(s.split())",
     "def word_count(s):\n    out = {}\n    for w in s.split():\n        out[w] = out.get(w, 0) + 1\n"
     "    return out"),
    ("median", "median(xs)", "returns the median of the non-empty list of numbers xs",
     ["median([1, 2, 9]) == 2", "median([7]) == 7"], ["median([1, 2, 3, 4]) == 2.5"],
     "def median(xs):\n    s = sorted(xs)\n    m = len(s) // 2\n    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2",
     "def median(xs):\n    return sum(xs) / len(xs)",
     "def median(xs):\n    return sorted(xs)[len(xs) // 2]"),
    ("title_case", "title_case(s)", "capitalizes the first letter of each space-separated word and lowercases the rest",
     ["title_case('hello world') == 'Hello World'", "title_case('a') == 'A'"],
     ["title_case(\"it's ok\") == \"It's Ok\""],
     "def title_case(s):\n    return ' '.join(w.capitalize() for w in s.split(' '))",
     "def title_case(s):\n    return s.upper()",
     "def title_case(s):\n    return s.title()"),
    ("gcd", "gcd(a, b)", "returns the greatest common divisor of two positive integers",
     ["gcd(4, 8) == 4", "gcd(5, 10) == 5"], ["gcd(12, 18) == 6", "gcd(7, 3) == 1"],
     "def gcd(a, b):\n    while b:\n        a, b = b, a % b\n    return a",
     "def gcd(a, b):\n    return a * b",
     "def gcd(a, b):\n    return min(a, b)"),
    ("second_largest", "second_largest(xs)", "returns the second largest distinct value in xs",
     ["second_largest([1, 3, 2]) == 2", "second_largest([10, 20]) == 10"],
     ["second_largest([5, 5, 3]) == 3"],
     "def second_largest(xs):\n    return sorted(set(xs))[-2]",
     "def second_largest(xs):\n    return sorted(xs)[-1]",
     "def second_largest(xs):\n    return sorted(xs)[-2]"),
]


def fence(code: str) -> str:
    return f"```python\n{code}\n```"


def code_prompt(sig, desc, visible) -> str:
    lines = "\n".join(f"assert {v}" for v in visible)
    return (f"Write a Python function `{sig}` that {desc}.\nExamples:\n{lines}\n"
            "Return only the code in one python block.")


def write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def build_code_tasks():
    cases, bank = [], {}
    for name, sig, desc, visible, hidden, good, bad_v, bad_h in CODE_TASKS:
        prompt = code_prompt(sig, desc, visible)
        tests = "\n".join(f"assert {t}" for t in visible + hidden)
        cases.append({"id": f"code-{name}", "input": prompt,
                      "checker": {"type": "unittest", "tests": tests}})
        bank[prompt] = {"good": [fence(good)], "bad": [fence(bad_v), fence(bad_h)]}
        checker = {"type": "unittest", "tests": tests}
        assert check(checker, fence(good)).passed, name
        assert not check(checker, fence(bad_v)).passed, name
        assert not check(checker, fence(bad_h)).passed, name
        vis = {"type": "unittest", "tests": "\n".join(f"assert {t}" for t in visible)}
        assert not check(vis, fence(bad_v)).passed, f"{name}: bad_v must fail a visible test"
        assert check(vis, fence(bad_h)).passed, f"{name}: bad_h must pass the visible tests"
    d = ROOT / "examples" / "code_tasks"
    write_jsonl(d / "cases.jsonl", cases)
    (d / "fake_bank.json").write_text(json.dumps(bank, indent=2, sort_keys=True) + "\n")
    return cases


FIRST = ["Dana", "Lee", "Priya", "Omar", "Mina", "Jon", "Ada", "Kofi", "Sara", "Ravi", "Ines", "Tom"]
LAST = ["Ruiz", "Park", "Nair", "Haddad", "Chen", "Berg", "Lovel", "Mensah", "Kaya", "Iyer", "Costa", "Vale"]
ITEMS = ["blue mug", "desk lamp", "notebook", "water bottle", "phone stand", "tea set", "backpack", "pen case"]
CITIES = ["Austin", "Leeds", "Pune", "Lyon", "Osaka", "Denver", "Porto", "Accra"]

ORDER_SCHEMA = {
    "type": "object",
    "required": ["order_id", "customer", "quantity", "item", "city"],
    "properties": {
        "order_id": {"type": "integer"},
        "customer": {"type": "string"},
        "quantity": {"type": "integer"},
        "item": {"type": "string", "enum": ITEMS},
        "city": {"type": "string"},
    },
}


def build_json_extract():
    rng = random.Random(SEED)
    cases, bank = [], {}
    for i in range(20):
        truth = {"order_id": rng.randint(1000, 9999),
                 "customer": f"{rng.choice(FIRST)} {rng.choice(LAST)}",
                 "quantity": rng.randint(1, 9), "item": rng.choice(ITEMS), "city": rng.choice(CITIES)}
        text = (f"Order {truth['order_id']} from {truth['customer']}: {truth['quantity']} x "
                f"{truth['item']}, ship to {truth['city']}.")
        prompt = ("Extract the order as JSON with keys order_id (integer), customer, quantity "
                  "(integer), item and city. Reply with JSON only.\n\nText: " + text)
        wrong_type = {**truth, "quantity": str(truth["quantity"])}
        missing = {k: v for k, v in truth.items() if k != "city"}
        wrong_value = {**truth, "order_id": truth["order_id"] + 1}
        bank[prompt] = {"good": [json.dumps(truth)],
                        "bad": [json.dumps(wrong_type), json.dumps(missing), json.dumps(wrong_value)]}
        cases.append({"id": f"order-{i:02d}", "input": prompt,
                      "checker": {"type": "json_schema", "schema": ORDER_SCHEMA}, "ground_truth": truth})
    d = ROOT / "examples" / "json_extract"
    write_jsonl(d / "cases.jsonl", cases)
    (d / "fake_bank.json").write_text(json.dumps(bank, indent=2, sort_keys=True) + "\n")


MATH_CHECKER = {"type": "regex", "pattern": r"Final answer: (-?\d+)"}


def build_judge_cases():
    rng = random.Random(SEED)
    rows = []
    # 24 math questions. Some answers carry a distracting number after the final answer.
    for i in range(24):
        a, b, c = rng.randint(11, 60), rng.randint(2, 40), rng.randint(2, 9)
        expr = [f"({a} + {b}) * {c}", f"{a} * {c} - {b}", f"({a} - {b}) * {c} + {b}"][i % 3]
        value = eval(expr, {"__builtins__": {}})  # noqa: S307 (our own integer expression)
        wrong = value + rng.choice([-10, -2, -1, 1, 2, 10])
        q = ("What is the value of the expression below? Give the final answer as an integer.\n"
             f"Compute: {expr}")
        right_text = f"I work it out step by step.\nFinal answer: {value}"
        wrong_text = f"I work it out step by step.\nFinal answer: {wrong}"
        if i % 6 == 0:
            right_text += f" (my first try gave {wrong})"
        if i % 8 == 3:
            wrong_text += f" (close to {value})"
        for kind, text in (("right", right_text), ("wrong", wrong_text)):
            label = check(MATH_CHECKER, text, ground_truth=value).passed
            rows.append({"id": f"math-{i:02d}-{kind}", "pair_id": f"math-{i:02d}", "task_type": "math",
                         "question": q, "candidate": text, "label": label})
    # 12 code questions from the code tasks. Half the wrong answers pass the visible examples.
    for j, (name, sig, desc, visible, hidden, good, bad_v, bad_h) in enumerate(CODE_TASKS[:12]):
        q = code_prompt(sig, desc, visible)
        tests = "\n".join(f"assert {t}" for t in visible + hidden)
        wrong = bad_h if j % 2 == 0 else bad_v
        for kind, code in (("right", good), ("wrong", wrong)):
            text = fence(code)
            label = check({"type": "unittest", "tests": tests}, text).passed
            rows.append({"id": f"code-{name}-{kind}", "pair_id": f"code-{name}", "task_type": "code",
                         "question": q, "candidate": text, "label": label})
    for r in rows:
        assert r["label"] == r["id"].endswith("-right"), r["id"]
    write_jsonl(ROOT / "examples" / "judge_calibration" / "judge_cases.jsonl", rows)
    return rows


if __name__ == "__main__":
    build_code_tasks()
    build_json_extract()
    rows = build_judge_cases()
    print(f"code tasks: {len(CODE_TASKS)}, json cases: 20, judge cases: {len(rows)}")
