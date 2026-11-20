"""Load eval cases from JSON Lines files."""

import json
from dataclasses import dataclass, field
from pathlib import Path

CHECKER_TYPES = ("exact", "regex", "json_schema", "unittest")


@dataclass(frozen=True)
class Case:
    id: str
    input: str
    checker: dict
    ground_truth: object = None
    meta: dict = field(default_factory=dict)


def load_cases(path) -> list[Case]:
    """Read one case per line. Blank lines are skipped. Ids must be unique."""
    cases: list[Case] = []
    seen: set[str] = set()
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f"{path}:{n}: bad JSON: {e}") from e
        for key in ("id", "input", "checker"):
            if key not in raw:
                raise ValueError(f"{path}:{n}: missing {key!r}")
        if raw["checker"].get("type") not in CHECKER_TYPES:
            raise ValueError(f"{path}:{n}: unknown checker type {raw['checker'].get('type')!r}")
        if raw["id"] in seen:
            raise ValueError(f"{path}:{n}: duplicate id {raw['id']!r}")
        seen.add(raw["id"])
        cases.append(
            Case(
                id=str(raw["id"]),
                input=raw["input"],
                checker=raw["checker"],
                ground_truth=raw.get("ground_truth"),
                meta=raw.get("meta", {}),
            )
        )
    return cases
