import pytest

from calibra_eval.canon import canonical_json, request_key
from calibra_eval.fixtures import CachedModel, FixtureStore, MissingFixture


def test_canonical_json_is_sorted_and_compact():
    assert canonical_json({"b": 1, "a": [1, {"d": 2, "c": 3}]}) == '{"a":[1,{"c":3,"d":2}],"b":1}'


def test_key_ignores_key_order():
    """Broken case: hashing json.dumps without sort_keys gives two keys for one request."""
    a = {"model": "m", "messages": [{"role": "user", "content": "hi"}], "seed": 1}
    b = {"seed": 1, "messages": [{"content": "hi", "role": "user"}], "model": "m"}
    assert request_key(a) == request_key(b)
    assert len(request_key(a)) == 64


def test_record_then_replay(tmp_path):
    calls = []

    def client(req):
        calls.append(req)
        return {"text": "hello", "prompt_tokens": 1, "completion_tokens": 1}

    path = tmp_path / "fx.jsonl"
    store = FixtureStore(path)
    rec = CachedModel(client, store, "record", recorded_on="2026-11-20")
    req = {"model": "m", "messages": [], "seed": 1}
    r1 = rec(req)
    r2 = rec(req)
    assert len(calls) == 1 and r1 == r2 and r1["recorded_on"] == "2026-11-20"
    store.save()

    replay = CachedModel(lambda r: pytest.fail("replay must not call the client"),
                         FixtureStore(path), "replay")
    assert replay(req)["text"] == "hello"
    with pytest.raises(MissingFixture):
        replay({"model": "m", "messages": [], "seed": 2})


def test_save_is_sorted_and_stable(tmp_path):
    path = tmp_path / "fx.jsonl"
    store = FixtureStore(path)
    for i in (3, 1, 2):
        store.put({"i": i}, {"text": str(i)})
    store.save()
    first = path.read_bytes()
    FixtureStore(path).save()
    assert path.read_bytes() == first
    keys = [line.split('"key":"')[1][:64] for line in first.decode().splitlines()]
    assert keys == sorted(keys)


def test_bad_mode():
    with pytest.raises(ValueError):
        CachedModel(lambda r: r, FixtureStore("x.jsonl"), "live")
