import pytest

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_save(database):
    doc = await database.get("foo42")
    doc["bar"] = True
    await doc.save()

    keys = [key async for key in database.akeys()]

    assert "foo42" in keys
    assert len(keys) == 1


async def test_fetch_dirty_document(database):
    doc = await database.get("foo")

    doc["dirty"] = "shitz"
    with pytest.raises(ValueError):
        await doc.fetch()


async def test_get_for_existing(filled_database):
    doc = await filled_database.get("foo")

    assert doc["bar"] is True
    assert doc["_id"] == doc.id == "foo"
    assert doc["_rev"].startswith("1-")
    assert doc._dirty_cache is False


async def test_get_for_non_existing(database):
    doc = await database.get("foo")

    assert doc["_id"] == doc.id == "foo"
    assert doc._dirty_cache is True
    assert "_rev" not in doc


async def test_save_with_data(database):
    doc = await database.get("foo")

    doc["blub"] = "blubber"

    await doc.save()

    assert doc["_id"] == doc.id == "foo"
    assert doc["_rev"].startswith("1-")
    assert doc._dirty_cache is False

    del database._document_cache["foo"]

    doc = await database.get("foo")
    assert doc["_id"] == doc.id == "foo"
    assert doc["_rev"].startswith("1-")
    assert doc["blub"] == "blubber"
    assert doc._dirty_cache is False


async def test_update(filled_database):
    doc = await filled_database.get("foo")

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

    del filled_database._document_cache["foo"]

    doc = await filled_database.get("foo")
    assert doc["_id"] == doc.id == "foo"
    assert doc["_rev"].startswith("2-")
    assert doc._dirty_cache is False
    assert doc["blub"] == "blubber"
    assert "bar" not in doc


async def test_delete(filled_database):
    doc = await filled_database.get("foo")

    await doc.delete()

    keys = [key async for key in filled_database.akeys()]

    assert len(keys) == 3
    assert sorted(keys) == ["baz", "baz2", "foo2"]


async def test_delete_dirty(filled_database):
    doc = await filled_database.get("foo")

    doc["fuzzy"] = "lizzy"

    with pytest.raises(ValueError):
        await doc.delete()


async def test_copy(filled_database):
    foo = await filled_database.get("foo")
    foo_copy = await foo.copy("foo_copy")

    assert foo_copy._cached_data.keys() == foo._cached_data.keys()
    for key in foo_copy._cached_data.keys():
        if key == "_id":
            continue
        assert foo_copy[key] == foo[key]
    assert foo_copy == await filled_database.get("foo_copy")


async def test_fetch_non_existant(database):
    doc = await database.get("foo")

    with pytest.raises(RuntimeError):
        await doc.fetch(discard_changes=True)


async def test_multiple_doc_keep_in_sync(filled_database):
    from aiocouch.document import Document

    doc1 = await filled_database.get("foo")

    new_ref = None
    doc2 = None

    async for doc in filled_database.find({"_id": "foo"}):
        assert isinstance(doc, Document)

        doc["blub"] = "blubber"
        await doc.save()
        new_ref = doc["_rev"]
        doc2 = doc

    assert new_ref is not None
    assert doc2 is not None
    assert doc1 == doc2
