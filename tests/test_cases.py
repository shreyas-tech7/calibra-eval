import json

import pytest

from calibra_eval.cases import load_cases


def _write(tmp_path, rows):
    p = tmp_path / "cases.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n\n")
    return p


def test_loads_cases_and_skips_blank_lines(tmp_path):
    p = _write(tmp_path, [{"id": "a", "input": "hi", "checker": {"type": "exact", "expected": "hi"}},
                          {"id": "b", "input": "x", "checker": {"type": "regex", "pattern": "x"},
                           "ground_truth": "x", "meta": {"k": 1}}])
    cases = load_cases(p)
    assert [c.id for c in cases] == ["a", "b"]
    assert cases[1].ground_truth == "x" and cases[1].meta == {"k": 1}


@pytest.mark.parametrize("row,msg", [
    ({"id": "a", "input": "x"}, "missing 'checker'"),
    ({"id": "a", "input": "x", "checker": {"type": "llm"}}, "unknown checker"),
])
def test_rejects_bad_cases(tmp_path, row, msg):
    with pytest.raises(ValueError, match=msg):
        load_cases(_write(tmp_path, [row]))


def test_rejects_duplicate_ids(tmp_path):
    row = {"id": "a", "input": "x", "checker": {"type": "exact", "expected": "x"}}
    with pytest.raises(ValueError, match="duplicate"):
        load_cases(_write(tmp_path, [row, row]))
