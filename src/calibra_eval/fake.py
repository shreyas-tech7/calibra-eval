"""Deterministic fake models. They are simulators, not language models.

They let every test and example run offline. Each answer depends only on the request,
so the same request always gives the same answer.
"""

import ast
import json
import operator
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from .canon import unit_float
from .checkers import clean_env

# Base chance that a bank-driven fake model picks a correct answer for a sample.
PROFILES = {
    "fake:coder-strong": 0.85,
    "fake:coder-weak": 0.55,
    "fake:extractor": 0.80,
}

# Every question gets a shared difficulty in [0, 1). Hard questions are hard for every fake
# model, as with real models. That makes two models' scores correlate across questions.
DIFFICULTY_SPREAD = 0.6

JUDGE_NAME = "fake:judge-sim"
JUDGE_NOISE = 0.06  # chance to flip a pointwise verdict
JUDGE_LONG_CHARS = 350  # answers longer than this get the designed verbosity lean
JUDGE_VERBOSE_ACCEPT = 0.40  # chance to accept a long answer it believes is wrong
JUDGE_POSITION_A = 0.12  # chance to answer "A" without looking, in pairwise mode
JUDGE_PAIR_NOISE = 0.05  # chance to flip a pairwise pick


def words(text: str) -> int:
    return len(text.split())


def _user_text(request: dict) -> str:
    users = [m["content"] for m in request.get("messages", []) if m.get("role") == "user"]
    return users[-1] if users else ""


class FakeModel:
    """Call it like a client: request dict in, response dict out."""

    def __init__(self, name: str, bank: dict | None = None):
        if name != JUDGE_NAME and name not in PROFILES:
            raise ValueError(f"unknown fake model {name!r}")
        self.name = name
        self.bank = bank or {}

    @classmethod
    def from_bank_file(cls, name: str, path):
        bank = json.loads(Path(path).read_text(encoding="utf-8")) if path else {}
        return cls(name, bank)

    def __call__(self, request: dict) -> dict:
        prompt = _user_text(request)
        if self.name == JUDGE_NAME:
            text = judge_sim(prompt)
        else:
            text = self._bank_answer(prompt, request.get("seed", 0))
        system = " ".join(m["content"] for m in request.get("messages", []) if m["role"] != "user")
        return {
            "text": text,
            "model": self.name,
            "prompt_tokens": words(system) + words(prompt),
            "completion_tokens": words(text),
            "tokens_exact": False,
        }

    def _bank_answer(self, prompt: str, seed) -> str:
        entry = self.bank.get(prompt)
        if entry is None:
            return "I do not know."
        difficulty = unit_float("difficulty", prompt)
        p_good = PROFILES[self.name] - DIFFICULTY_SPREAD * (difficulty - 0.5)
        p_good = min(0.98, max(0.02, p_good))
        u = unit_float(self.name, prompt, seed)
        pool = entry["good"] if u < p_good or not entry["bad"] else entry["bad"]
        return pool[int(unit_float("pick", self.name, prompt, seed) * len(pool))]


_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}


def safe_eval(expr: str) -> int:
    """Evaluate integer arithmetic (+ - * // %) without eval()."""

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -ev(node.operand)
        raise ValueError(f"unsupported expression: {expr!r}")

    return ev(ast.parse(expr, mode="eval"))


def _between(text: str, start: str, end: str) -> str:
    i = text.index(start) + len(start)
    j = text.index(end, i)
    return text[i:j]


def _runs_visible_tests(question: str, answer: str) -> bool:
    asserts = [ln for ln in question.splitlines() if ln.startswith("assert ")]
    m = re.search(r"```(?:python)?\s*\n(.*?)```", answer, re.S)
    code = m.group(1) if m else answer
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "judge_check.py"
        script.write_text(code + "\n" + "\n".join(asserts) + "\n", encoding="utf-8")
        try:
            proc = subprocess.run([sys.executable, "-I", str(script)], cwd=tmp, env=clean_env(),
                                  capture_output=True, timeout=5)
        except subprocess.TimeoutExpired:
            return False
    return proc.returncode == 0


def belief(question: str, answer: str) -> bool:
    """What the simulated judge thinks before noise. It can be wrong for real reasons:
    it reads the last number in a math answer, and it runs only the visible code tests."""
    m = re.search(r"Compute: (.+)", question)
    if m:
        nums = re.findall(r"-?\d+", answer)
        return bool(nums) and int(nums[-1]) == safe_eval(m.group(1).strip())
    return _runs_visible_tests(question, answer)


def judge_sim(prompt: str) -> str:
    if "Answer A:\n" in prompt:
        question = _between(prompt, "Question:\n", "\n\nAnswer A:\n")
        a = _between(prompt, "Answer A:\n", "\n\nAnswer B:\n")
        b = _between(prompt, "Answer B:\n", "\n\nWhich answer")
        if unit_float("posA", prompt) < JUDGE_POSITION_A:
            return "A"
        ba, bb = belief(question, a), belief(question, b)
        if ba == bb:
            return "A"  # designed tie-break: a source of position bias
        pick = "A" if ba else "B"
        if unit_float("pairnoise", prompt) < JUDGE_PAIR_NOISE:
            pick = "B" if pick == "A" else "A"
        return pick
    question = _between(prompt, "Question:\n", "\n\nAnswer:\n")
    answer = _between(prompt, "Answer:\n", "\n\nReply with")
    ok = belief(question, answer)
    if not ok and len(answer) > JUDGE_LONG_CHARS and unit_float("verbose", prompt) < JUDGE_VERBOSE_ACCEPT:
        ok = True
    if unit_float("noise", prompt) < JUDGE_NOISE:
        ok = not ok
    return "CORRECT" if ok else "INCORRECT"
