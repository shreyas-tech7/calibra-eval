"""Canonical JSON and hashing. One place, so every key is made the same way."""

import hashlib
import json


def canonical_json(obj) -> str:
    """Sorted keys, no extra spaces. The brief fixes this format for fixture keys."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def request_key(request: dict) -> str:
    """Fixture key: SHA-256 of the canonical request JSON."""
    return sha256_hex(canonical_json(request))


def unit_float(*parts) -> float:
    """A repeatable number in [0, 1) made from the parts. Used by the fake models."""
    h = sha256_hex("|".join(str(p) for p in parts))
    return int(h[:13], 16) / float(1 << 52)
