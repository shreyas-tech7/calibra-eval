"""One small adapter for any OpenAI-compatible chat endpoint, built on urllib."""

import json
import os
import time
import urllib.error
import urllib.request


class ProviderError(RuntimeError):
    pass


class OpenAICompatible:
    """POST {base_url}/chat/completions. The key comes from an environment variable, if set."""

    def __init__(self, base_url: str, api_key_env: str = "LLM_API_KEY", timeout_s: float = 60,
                 max_tries: int = 5, first_wait_s: float = 2.0, sleep=time.sleep, opener=None):
        if not base_url.startswith(("https://", "http://")):
            raise ValueError(f"base_url must start with https:// or http://, got {base_url!r}")
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.api_key_env = api_key_env
        self.timeout_s = timeout_s
        self.max_tries = max_tries
        self.first_wait_s = first_wait_s
        self.sleep = sleep
        self.opener = opener or urllib.request.urlopen

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        key = os.environ.get(self.api_key_env, "")
        if key:
            headers["Authorization"] = f"Bearer {key}"
        return headers

    def __call__(self, request: dict) -> dict:
        body = json.dumps(request).encode("utf-8")
        wait = self.first_wait_s
        for attempt in range(1, self.max_tries + 1):
            req = urllib.request.Request(self.url, data=body, headers=self._headers(), method="POST")
            try:
                with self.opener(req, timeout=self.timeout_s) as resp:  # noqa: S310 (scheme checked)
                    data = json.loads(resp.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as e:
                if (e.code == 429 or e.code >= 500) and attempt < self.max_tries:
                    self.sleep(wait)
                    wait *= 2
                    continue
                raise ProviderError(f"HTTP {e.code} from {self.url}") from e
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt < self.max_tries:
                    self.sleep(wait)
                    wait *= 2
                    continue
                raise ProviderError(f"no response from {self.url}: {e}") from e
        usage = data.get("usage") or {}
        return {
            "text": data["choices"][0]["message"]["content"],
            "model": data.get("model", request.get("model")),
            "prompt_tokens": int(usage.get("prompt_tokens", 0)),
            "completion_tokens": int(usage.get("completion_tokens", 0)),
            "tokens_exact": bool(usage),
        }
