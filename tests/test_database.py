import pytest

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_create_document(database):
    doc = await database.get("test_document")

    # doc not yet saved, so it shouldn't be listed in the database
    assert doc.id not in [key async for key in database.akeys()]

    await doc.save()

    # doc was saved, so it should be listed in the database
    assert doc.id in [key async for key in database.akeys()]


async def test_save_all(filled_database):
    keys = [key async for key in filled_database.akeys()]

    assert len(keys) == 4
    assert sorted(keys) == ["baz", "baz2", "foo", "foo2"]


async def test_save_all_filtered(database):
    await database.save_all([await database.get("foobar")])

    keys = [key async for key in database.akeys()]

    assert len(keys) == 1
    assert sorted(keys) == ["foobar"]


async def test_get_all_on_empty(database):
    all_docs = [doc async for doc in database.get_all([])]

    assert all_docs == []


async def test_get_all_filtered(filled_database):
    all_docs = [doc async for doc in filled_database.get_all(["foo", "baz"])]

    assert len(all_docs) == 2
    assert await filled_database.get("foo") in all_docs
    assert await filled_database.get("baz") in all_docs


async def test_get_all_filtered_empty(filled_database):
    all_docs = [doc async for doc in filled_database.get_all([])]

    assert len(all_docs) == 0


async def test_get_all_on_non_existant(database):
    docs = [doc async for doc in database.get_all("foo")]

    assert len(docs) == 1
    doc = docs[0]
    assert doc._dirty_cache is True
    assert doc.id == "foo"


async def test_find(filled_database):
    matching_docs = [
        doc
        async for doc in filled_database.find(
            {"bar": True, "fields": "ignored"}, limit=1
        )
    ]

    assert len(matching_docs) == 3

    from aiocouch.document import Document

    for doc in matching_docs:
        assert isinstance(doc, Document)

    assert await filled_database.get("foo") in matching_docs
    assert await filled_database.get("foo2") in matching_docs
    assert await filled_database.get("baz2") in matching_docs
