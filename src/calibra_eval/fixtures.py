"""Record and replay. Each model call is saved under the SHA-256 of its canonical request."""

import json
import threading
import time
from pathlib import Path

from .canon import canonical_json, request_key


class MissingFixture(KeyError):
    """Replay mode met a request that was never recorded."""


class FixtureStore:
    """A JSON Lines file of {key, request, response}, written sorted by key."""

    def __init__(self, path):
        self.path = Path(path)
        self._lock = threading.Lock()
        self._items: dict[str, dict] = {}
        self.dirty = False
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    item = json.loads(line)
                    self._items[item["key"]] = item

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, request: dict) -> bool:
        return request_key(request) in self._items

    def get(self, request: dict) -> dict:
        key = request_key(request)
        with self._lock:
            if key not in self._items:
                raise MissingFixture(f"no fixture for request key {key}")
            return self._items[key]["response"]

    def put(self, request: dict, response: dict) -> None:
        key = request_key(request)
        with self._lock:
            self._items[key] = {"key": key, "request": request, "response": response}
            self.dirty = True

    def dates(self) -> list[str]:
        """The distinct recorded_on dates of the stored responses."""
        found = {item["response"].get("recorded_on", "") for item in self._items.values()}
        return sorted(found - {""})

    def save(self) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            lines = [canonical_json(self._items[k]) for k in sorted(self._items)]
            self.path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
            self.dirty = False


class CachedModel:
    """Wrap a model client. Replay reads fixtures only. Record calls the client for new requests."""

    def __init__(self, client, store: FixtureStore, mode: str = "replay", recorded_on: str = ""):
        if mode not in ("replay", "record"):
            raise ValueError(f"mode must be replay or record, not {mode!r}")
        self.client = client
        self.store = store
        self.mode = mode
        self.recorded_on = recorded_on or time.strftime("%Y-%m-%d", time.gmtime())

    def __call__(self, request: dict) -> dict:
        if request in self.store:
            return self.store.get(request)
        if self.mode == "replay":
            raise MissingFixture(
                f"replay mode: no fixture for request key {request_key(request)}. "
                "Run with --record to create it."
            )
        start = time.perf_counter()
        response = self.client(request)
        response = dict(response)
        response["latency_ms"] = round((time.perf_counter() - start) * 1000, 3)
        response["recorded_on"] = self.recorded_on
        self.store.put(request, response)
        return response
