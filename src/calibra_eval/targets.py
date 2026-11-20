"""Targets: a Python function, a shell command or a model."""

import importlib.util
import json
import os
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from .adapter import OpenAICompatible
from .fake import FakeModel
from .fixtures import CachedModel, FixtureStore

SHELL_TIMEOUT_S = 30


@dataclass(frozen=True)
class Output:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0
    model: str = ""
    tokens_exact: bool = False


def _load_function(ref: str, base: Path):
    """'path/to/file.py:func' or 'package.module:func'."""
    mod_ref, func = ref.split(":")
    if mod_ref.endswith(".py"):
        path = (base / mod_ref).resolve()
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        module = importlib.import_module(mod_ref)
    return getattr(module, func)


class FunctionTarget:
    def __init__(self, spec: dict, base: Path):
        self.id = f"python:{spec['function']}"
        self.fn = _load_function(spec["function"], base)

    def __call__(self, case_input, sample: int) -> Output:
        start = time.perf_counter()
        text = str(self.fn(case_input))
        return Output(text, latency_ms=round((time.perf_counter() - start) * 1000, 3))


class ShellTarget:
    """Runs the command with the case input as JSON on stdin. The output is stdout."""

    def __init__(self, spec: dict, base: Path):
        cmd = spec["command"]
        self.argv = shlex.split(cmd) if isinstance(cmd, str) else list(cmd)
        self.cwd = base
        self.timeout = spec.get("timeout_s", SHELL_TIMEOUT_S)
        self.id = "shell:" + " ".join(self.argv)

    def __call__(self, case_input, sample: int) -> Output:
        start = time.perf_counter()
        proc = subprocess.run(self.argv, input=json.dumps(case_input), capture_output=True,
                              text=True, cwd=self.cwd, timeout=self.timeout)
        return Output(proc.stdout, latency_ms=round((time.perf_counter() - start) * 1000, 3))


class ModelTarget:
    def __init__(self, spec: dict, base: Path, store: FixtureStore, mode: str, seed: int,
                 recorded_on: str = ""):
        self.model = spec["model"]
        self.id = f"model:{self.model}"
        self.system = spec.get("system", "")
        self.prompt = spec.get("prompt", "{input}")
        self.temperature = spec.get("temperature", 0.0)
        self.max_tokens = spec.get("max_tokens", 512)
        self.seed = seed
        if self.model.startswith("fake:"):
            bank = spec.get("fake_bank")
            client = FakeModel.from_bank_file(self.model, base / bank if bank else None)
        else:
            base_url = spec.get("base_url") or os.environ.get("LLM_BASE_URL", "")
            if not base_url:
                raise ValueError("model target needs base_url or LLM_BASE_URL")
            client = OpenAICompatible(base_url, spec.get("api_key_env", "LLM_API_KEY"))
        self.call = CachedModel(client, store, mode, recorded_on)

    def request(self, case_input, sample: int) -> dict:
        messages = []
        if self.system:
            messages.append({"role": "system", "content": self.system})
        messages.append({"role": "user", "content": self.prompt.format(input=case_input)})
        return {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "seed": self.seed * 1000 + sample,
        }

    def __call__(self, case_input, sample: int) -> Output:
        r = self.call(self.request(case_input, sample))
        return Output(r["text"], r.get("prompt_tokens", 0), r.get("completion_tokens", 0),
                      r.get("latency_ms", 0.0), r.get("model", self.model),
                      r.get("tokens_exact", False))


def make_target(spec: dict, base: Path, store: FixtureStore | None = None, mode: str = "replay",
                seed: int = 1, recorded_on: str = ""):
    kind = spec.get("type", "model")
    if kind == "python":
        return FunctionTarget(spec, base)
    if kind == "shell":
        return ShellTarget(spec, base)
    if kind == "model":
        if store is None:
            raise ValueError("model target needs a fixture store")
        return ModelTarget(spec, base, store, mode, seed, recorded_on)
    raise ValueError(f"unknown target type {kind!r}")

