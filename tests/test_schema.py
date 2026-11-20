from calibra_eval.schema import validate

SCHEMA = {
    "type": "object",
    "required": ["name", "tags"],
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "tags": {"type": "array", "items": {"type": "string", "enum": ["a", "b"]}},
    },
}


def test_valid_instance():
    assert validate({"name": "x", "age": 3, "tags": ["a"]}, SCHEMA) == []


def test_missing_required_and_wrong_types():
    """Broken case: a checker that only looks at `type` would accept these."""
    errs = validate({"name": 5, "tags": ["c", 1]}, SCHEMA)
    assert any("$.name" in e for e in errs)
    assert any("$.tags[0]" in e and "enum" in e for e in errs)
    assert any("$.tags[1]" in e for e in errs)


def test_bool_is_not_integer():
    assert validate(True, {"type": "integer"}) != []
    assert validate(2.5, {"type": "number"}) == []
    assert validate(None, {"type": ["string", "null"]}) == []
