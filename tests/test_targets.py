import sys

import pytest

from calibra_eval.fixtures import FixtureStore
from calibra_eval.targets import make_target


def test_python_target(tmp_path):
    (tmp_path / "mod.py").write_text("def run(x):\n    return x.upper()\n")
    t = make_target({"type": "python", "function": "mod.py:run"}, tmp_path)
    assert t("abc", 0).text == "ABC"


def test_shell_target(tmp_path):
    cmd = [sys.executable, "-c", "import json,sys; print(json.load(sys.stdin)[::-1])"]
    t = make_target({"type": "shell", "command": cmd}, tmp_path)
    assert t("abc", 0).text.strip() == "cba"


def test_model_target_request_shape_and_replay(tmp_path):
    store = FixtureStore(tmp_path / "fx.jsonl")
    spec = {"type": "model", "model": "fake:extractor", "system": "sys", "prompt": "Q: {input}"}
    rec = make_target(spec, tmp_path, store, "record", seed=1, recorded_on="2026-11-20")
    req = rec.request("hello", 2)
    assert req["seed"] == 1002
    assert req["messages"] == [{"role": "system", "content": "sys"},
                               {"role": "user", "content": "Q: hello"}]
    out = rec("hello", 2)
    store.save()
    rep = make_target(spec, tmp_path, FixtureStore(tmp_path / "fx.jsonl"), "replay", seed=1)
    assert rep("hello", 2) == out


def test_model_target_needs_store_and_url(tmp_path, monkeypatch):
    with pytest.raises(ValueError):
        make_target({"type": "model", "model": "fake:extractor"}, tmp_path)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    with pytest.raises(ValueError, match="base_url"):
        make_target({"type": "model", "model": "real-model"}, tmp_path, FixtureStore("x"))
    with pytest.raises(ValueError):
        make_target({"type": "rpc"}, tmp_path)
