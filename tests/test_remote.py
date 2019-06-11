def test_stringify_params():
    from aiocouch.remote import _stringify_params

    assert _stringify_params(None) is None

    params = {"foo": "bar", "baz": True, "boo": False, "foz": None}

    assert _stringify_params(params) == {"foo": "bar", "baz": "true", "boo": "false"}
