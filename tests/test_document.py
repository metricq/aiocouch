from aiocouch import ConflictError

import pytest

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_save(database):
    doc = await database.create("foo42")
    doc["bar"] = True
    await doc.save()

    keys = [key async for key in database.akeys()]

    assert "foo42" in keys
    assert len(keys) == 1


async def test_fetch_dirty_document(database):
    from aiocouch import ConflictError

    doc = await database.create("foo")

    doc["dirty"] = "shitz"
    with pytest.raises(ConflictError):
        await doc.fetch()


async def test_save_with_data(database):
    doc = await database.create("foo")

    doc["blub"] = "blubber"

    await doc.save()

    assert doc["_id"] == doc.id == "foo"
    assert doc["_rev"].startswith("1-")
    assert doc._dirty_cache is False

    doc = await database["foo"]
    assert doc["_id"] == doc.id == "foo"
    assert doc["_rev"].startswith("1-")
    assert doc["blub"] == "blubber"
    assert doc._dirty_cache is False


async def test_conflict(filled_database):
    doc1 = await filled_database["foo"]
    doc2 = await filled_database["foo"]

    doc1["blub"] = "new"
    await doc1.save()

    doc2["blub"] = "bar"

    with pytest.raises(ConflictError):
        await doc2.save()


async def test_update(filled_database):
    doc = await filled_database["foo"]

    assert doc["_rev"].startswith("1-")
    assert doc._dirty_cache is False

    del doc["bar"]
    doc["blub"] = "blubber"

    assert doc["_rev"].startswith("1-")
    assert doc._dirty_cache is True

    await doc.save()

    assert doc["_id"] == doc.id == "foo"
    assert doc["_rev"].startswith("2-")
    assert doc._dirty_cache is False

    doc = await filled_database["foo"]
    assert doc["_id"] == doc.id == "foo"
    assert doc["_rev"].startswith("2-")
    assert doc._dirty_cache is False
    assert doc["blub"] == "blubber"
    assert "bar" not in doc


async def test_delete(filled_database):
    doc = await filled_database["foo"]

    await doc.delete()

    keys = [key async for key in filled_database.akeys()]

    assert len(keys) == 3
    assert sorted(keys) == ["baz", "baz2", "foo2"]


async def test_delete_dirty(filled_database):
    from aiocouch import ConflictError

    doc = await filled_database["foo"]

    doc["fuzzy"] = "lizzy"

    with pytest.raises(ConflictError):
        await doc.delete()


async def test_copy(filled_database):
    foo = await filled_database["foo"]
    foo_copy = await foo.copy("foo_copy")

    assert foo_copy.data.keys() == foo.data.keys()
    for key in foo_copy.data.keys():
        if key == "_id":
            continue
        assert foo_copy[key] == foo[key]


async def test_doc_update(doc):
    assert "test" not in doc

    doc.update({"test": "value"})

    assert "test" in doc
    assert doc["test"] == "value"


async def test_doc_items_keys_values(doc):
    assert list(doc.keys()) == ["_id"]
    assert list(doc.values()) == ["foo"]
    assert dict(doc.items()) == {"_id": "foo"}


async def test_filled_doc_items_keys_values(doc):
    doc.update({"test": "value"})

    assert list(doc.keys()) == ["_id", "test"]
    assert list(doc.values()) == ["foo", "value"]
    assert dict(doc.items()) == {"_id": "foo", "test": "value"}


async def test_get(doc):
    assert doc.get("foo") is None
    with pytest.raises(KeyError):
        doc["foo"]

    assert doc.get("foo", "baz") == "baz"
    with pytest.raises(KeyError):
        doc["foo"]

    assert doc.setdefault("foo") is None
    assert doc["foo"] is None

    assert doc.setdefault("baz", "bar") == "bar"
    assert doc["baz"] == "bar"

    assert doc.setdefault("baz", "kitty") == "bar"
    assert doc["baz"] == "bar"


async def test_repr(doc):
    print(doc)


async def test_cache(doc):
    assert doc._dirty_cache is True

    await doc.save()

    assert doc._dirty_cache is False

    doc["foo"] = {"hello": "kitty"}

    assert doc._dirty_cache is True

    await doc.save()

    assert doc._dirty_cache is False

    doc["foo"]["llama"] = "juicy"

    assert doc._dirty_cache is True

    await doc.save()

    assert doc._dirty_cache is False
