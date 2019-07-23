import pytest

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_create_document(database):
    doc = await database.create("test_document")

    # doc not yet saved, so it shouldn't be listed in the database
    assert doc.id not in [key async for key in database.akeys()]

    await doc.save()

    # doc was saved, so it should be listed in the database
    assert doc.id in [key async for key in database.akeys()]

async def test_akeys_with_prefix(filled_database):
    keys = [key async for key in filled_database.akeys(prefix="ba")]

    assert(len(keys) == 2)
    assert (sorted(keys)) == ["baz", "baz2"]

async def test_saved_docs_in_filled_db(filled_database):
    keys = [key async for key in filled_database.akeys()]

    assert len(keys) == 4
    assert sorted(keys) == ["baz", "baz2", "foo", "foo2"]


async def test_update_docs_creating(database):
    async with database.update_docs(["foobar"], create=True):
        pass

    keys = [key async for key in database.akeys()]

    assert len(keys) == 1
    assert sorted(keys) == ["foobar"]


async def test_update_docs_creating_not_ok(database):
    with pytest.raises(KeyError):
        async with database.update_docs(["foobar"]):
            pass


async def test_update_docs(database):
    async with database.update_docs(["foo", "baz"], create=True) as docs:
        async for doc in docs:
            doc["llama"] = "awesome"

    keys = [key async for key in database.akeys()]

    assert len(keys) == 2
    assert sorted(keys) == ["baz", "foo"]

    async for doc in database.values():
        assert "llama" in doc
        assert doc["llama"] == "awesome"


async def test_update_docs_for_deleted(filled_database):
    doc = await filled_database["foo"]
    await doc.delete()

    async with filled_database.update_docs(["foo"], create=True) as docs:
        async for doc in docs:
            doc["llama"] = "awesome"

    doc = await filled_database["foo"]

    assert "_deleted" not in doc
    assert "_rev" in doc
    assert doc["_rev"].startswith("3-")
    assert doc["llama"] == "awesome"


async def test_docs_on_empty(database):
    all_docs = [doc async for doc in database.docs([])]

    assert all_docs == []


async def test_docs_filtered(filled_database):
    keys = [doc.id async for doc in filled_database.docs(["foo", "baz"])]

    assert len(keys) == 2
    assert "foo" in keys
    assert "baz" in keys


async def test_docs_on_non_existant(database):
    docs = [doc async for doc in database.docs(["foo"], create=True)]

    assert len(docs) == 1
    doc = docs[0]
    assert doc._dirty_cache is True
    assert doc.id == "foo"

async def test_docs_with_prefix(filled_database):
    keys = [doc.id async for doc in filled_database.docs(prefix="ba")]

    assert(len(keys) == 2)
    assert (sorted(keys)) == ["baz", "baz2"]

async def test_docs_on_deleted(filled_database):
    doc = await filled_database["foo"]
    await doc.delete()

    with pytest.raises(KeyError):
        async for doc in filled_database.docs(["foo"]):
            assert False

    async for doc in filled_database.docs(["foo"], create=True):
        assert doc.id == "foo"
        assert doc.exists is False

async def test_docs_with_no_ids(filled_database):
    keys = [doc.id async for doc in filled_database.docs()]

    assert len(keys) == 4
    assert sorted(keys) == ["baz", "baz2", "foo", "foo2"]

async def test_find(filled_database):
    matching_docs = [
        doc async for doc in filled_database.find({"bar": True, "fields": "ignored"})
    ]

    assert len(matching_docs) == 3

    from aiocouch.document import Document

    matching_keys = []
    for doc in matching_docs:
        assert isinstance(doc, Document)
        matching_keys.append(doc.id)

    assert "foo" in matching_keys
    assert "foo2" in matching_keys
    assert "baz2" in matching_keys


async def test_find_limited(filled_database):
    matching_docs = [
        doc
        async for doc in filled_database.find(
            {"bar": True, "fields": "ignored"}, limit=1
        )
    ]

    assert len(matching_docs) == 1

    from aiocouch.document import Document

    matching_keys = []
    for doc in matching_docs:
        assert isinstance(doc, Document)
        matching_keys.append(doc.id)

    assert "baz2" in matching_keys


async def test_values_for_filled(filled_database):
    keys = [doc.id async for doc in filled_database.values()]

    assert len(keys) == 4
    assert sorted(keys) == ["baz", "baz2", "foo", "foo2"]


async def test_values_for_filled_limited(filled_database):
    keys = [doc.id async for doc in filled_database.values(limit=1)]

    assert len(keys) == 1
    assert keys == ["baz"]
