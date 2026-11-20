import io
import json
import urllib.error

import pytest

from calibra_eval.adapter import OpenAICompatible, ProviderError
from calibra_eval.fake import FakeModel, belief, judge_sim, safe_eval


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _ok(_req, timeout):
    return FakeResp(json.dumps({"model": "m1", "choices": [{"message": {"content": "hi"}}],
                                "usage": {"prompt_tokens": 3, "completion_tokens": 1}}).encode())


def test_adapter_parses_openai_shape(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "secret-value")
    seen = {}

    def opener(req, timeout):
        seen["auth"] = req.get_header("Authorization")
        seen["url"] = req.full_url
        return _ok(req, timeout)

    a = OpenAICompatible("http://local.test/v1/", opener=opener)
    r = a({"model": "m1", "messages": []})
    assert r == {"text": "hi", "model": "m1", "prompt_tokens": 3, "completion_tokens": 1,
                 "tokens_exact": True}
    assert seen["url"] == "http://local.test/v1/chat/completions"
    assert seen["auth"] == "Bearer secret-value"


def test_adapter_sends_no_auth_without_key(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    seen = {}

    def opener(req, timeout):
        seen["auth"] = req.get_header("Authorization")
        return _ok(req, timeout)

    OpenAICompatible("http://local.test/v1", opener=opener)({"model": "m"})
    assert seen["auth"] is None


def test_adapter_backs_off_on_429_then_gives_up():
    waits = []

    def opener(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 429, "slow down", {}, None)

    a = OpenAICompatible("http://local.test/v1", opener=opener, sleep=waits.append, max_tries=5)
    with pytest.raises(ProviderError, match="429"):
        a({"model": "m"})
    assert waits == [2.0, 4.0, 8.0, 16.0]


def test_adapter_retries_server_errors_and_dropped_connections():
    waits, errors = [], [
        urllib.error.HTTPError("u", 503, "busy", {}, None),
        urllib.error.URLError("connection reset"),
        TimeoutError("read timed out"),
    ]

    def opener(req, timeout):
        if errors:
            raise errors.pop(0)
        return _ok(req, timeout)

    a = OpenAICompatible("http://local.test/v1", opener=opener, sleep=waits.append)
    assert a({"model": "m"})["text"] == "hi"
    assert waits == [2.0, 4.0, 8.0]


def test_adapter_does_not_retry_client_errors():
    waits = []

    def opener(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 401, "no", {}, None)

    with pytest.raises(ProviderError, match="401"):
        OpenAICompatible("http://local.test/v1", opener=opener, sleep=waits.append)({"model": "m"})
    assert waits == []


def test_fake_model_is_deterministic_and_uses_bank():
    bank = {"q": {"good": ["right"], "bad": ["wrong1", "wrong2"]}}
    m = FakeModel("fake:coder-weak", bank)
    req = {"model": "fake:coder-weak", "messages": [{"role": "user", "content": "q"}], "seed": 7}
    assert m(req) == m(req)
    texts = {m({**req, "seed": s})["text"] for s in range(40)}
    assert "right" in texts and texts & {"wrong1", "wrong2"}
    with pytest.raises(ValueError):
        FakeModel("fake:nope")


def test_safe_eval():
    assert safe_eval("(17 + 5) * 3 - 4 // 2") == 64
    with pytest.raises(ValueError):
        safe_eval("__import__('os')")


def test_judge_sim_reads_last_number():
    """The simulated judge can be fooled by a trailing number. That is a designed, real error."""
    q = "Compute: 2 + 3"
    assert belief(q, "Final answer: 5")
    assert not belief(q, "Final answer: 5 (not 6)")


def test_judge_sim_formats():
    p = ("You are grading an answer to a question.\n\nQuestion:\nCompute: 1 + 1\n\nAnswer:\n"
         "Final answer: 2\n\nReply with exactly one word: CORRECT or INCORRECT.")
    assert judge_sim(p) in ("CORRECT", "INCORRECT")
    pw = ("x\n\nQuestion:\nCompute: 1 + 1\n\nAnswer A:\nFinal answer: 3\n\nAnswer B:\n"
          "Final answer: 2\n\nWhich answer is correct? Reply with exactly one letter: A or B.")
    assert judge_sim(pw) in ("A", "B")


def test_adapter_rejects_non_http_schemes():
    """Broken case: urlopen would happily read file:///etc/passwd as a 'model response'."""
    for url in ("file:///etc", "ftp://x", "localhost:8000/v1"):
        with pytest.raises(ValueError, match="https://"):
            OpenAICompatible(url)
