import pytest

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_null_view_keys(filled_database_with_view):
    values = [
        key
        async for key in filled_database_with_view.view(
            "test_ddoc", "null_view"
        ).akeys()
    ]

    assert len(values) == 4

    assert values[0] == "baz"
    assert values[1] == "baz2"
    assert values[2] == "foo"
    assert values[3] == "foo2"


async def test_null_view_ids(filled_database_with_view):
    values = [
        key
        async for key in filled_database_with_view.view("test_ddoc", "null_view").ids()
    ]

    assert len(values) == 4

    assert values[0] == "baz"
    assert values[1] == "baz2"
    assert values[2] == "foo"
    assert values[3] == "foo2"


async def test_null_view_docs(filled_database_with_view):
    values = [
        doc.id
        async for doc in filled_database_with_view.view("test_ddoc", "null_view").docs()
    ]

    assert len(values) == 4

    assert values[0] == "baz"
    assert values[1] == "baz2"
    assert values[2] == "foo"
    assert values[3] == "foo2"


async def test_null_view_docs_with_deleted(filled_database_with_view):
    doc = await filled_database_with_view["baz"]
    await doc.delete()

    docs = [
        doc
        async for doc in filled_database_with_view.view("test_ddoc", "null_view").docs(
            ids=["baz"]
        )
    ]

    assert len(docs) == 0
