import pytest

from aiocouch.database import Database
from aiocouch.document import Document

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_update_docs_on_empty(database: Database) -> None:
    async with database.update_docs([]) as bulk:
        pass

    assert bulk._docs == []
    keys = [key async for key in database.akeys()]
    assert len(keys) == 0


async def test_update_docs_creating(database: Database) -> None:
    async with database.update_docs(["foobar"], create=True):
        pass

    keys = [key async for key in database.akeys()]

    assert len(keys) == 1
    assert sorted(keys) == ["foobar"]


async def test_update_docs_creating_not_ok(database: Database) -> None:
    with pytest.raises(KeyError):
        async with database.update_docs(["foobar"]):
            pass


async def test_update_docs(database: Database) -> None:
    async with database.update_docs(["foo", "baz"], create=True) as bulk:
        async for doc in bulk:
            doc["llama"] = "awesome"

    keys = [key async for key in database.akeys()]

    assert len(keys) == 2
    assert sorted(keys) == ["baz", "foo"]

    async for doc in database.values():
        assert "llama" in doc
        assert doc["llama"] == "awesome"


async def test_update_docs_no_change(filled_database: Database) -> None:
    async with filled_database.update_docs(["foo", "baz"]) as bulk:
        pass

    assert bulk.response == []


async def test_update_dont_crash_on_pristine_doc(filled_database: Database) -> None:
    doc = await filled_database["foo"]
    doc["llama"] = "awesome"
    await doc.save()

    async with filled_database.update_docs(["foo", "baz"], create=True) as bulk:
        async for doc in bulk:
            doc["llama"] = "awesome"


async def test_update_docs_for_deleted(filled_database: Database) -> None:
    doc = await filled_database["foo"]
    await doc.delete()

    async with filled_database.update_docs(["foo"], create=True) as bulk:
        async for doc in bulk:
            doc["llama"] = "awesome"

    doc = await filled_database["foo"]

    assert "_deleted" not in doc
    assert "_rev" in doc
    assert doc["_rev"].startswith("3-")
    assert doc["llama"] == "awesome"


async def test_update_docs_for_errored(filled_database: Database) -> None:
    doc = await filled_database["foo"]
    doc["something"] = 42
    async with filled_database.update_docs(["foo", "baz"]) as bulk:
        # provoke a conflict for document foo
        await doc.save()

        async for doc in bulk:
            doc["thing"] = 42

    assert bulk.response is not None
    assert len(bulk.response) == 2

    assert bulk.ok is not None
    assert len(bulk.ok) == 1
    doc_ok = bulk.ok[0]
    assert doc_ok.id == "baz"
    assert doc_ok["thing"] == 42
    assert doc_ok["_rev"].startswith("2-")

    assert bulk.error is not None
    assert len(bulk.error) == 1
    doc_err = bulk.error[0]
    assert doc_err.id == "foo"
    assert doc_err["_rev"].startswith("1-")
    assert "something" not in doc_err


async def test_create_docs_with_ids(database: Database) -> None:
    async with database.create_docs(["foo", "baz"]) as bulk:
        pass

    assert bulk.response is not None
    assert len(bulk.response) == 2

    keys = [key async for key in database.akeys()]

    assert len(keys) == 2
    assert sorted(keys) == ["baz", "foo"]


async def test_create_docs_with_create(database: Database) -> None:
    async with database.create_docs() as bulk:
        bulk.create("foo", data={"counter": 42})
        bulk.create("baz")

        with pytest.raises(ValueError):
            bulk.create("foo")

    assert bulk.response is not None
    assert len(bulk.response) == 2

    keys = [key async for key in database.akeys()]

    assert len(keys) == 2
    assert sorted(keys) == ["baz", "foo"]

    foo = await database["foo"]
    assert "counter" in foo
    assert foo["counter"] == 42


async def test_create_docs_with_create_duplicate(database: Database) -> None:
    async with database.create_docs() as bulk:
        foo = bulk.create("foo")

        # DO NOT DO THIS! This is just using the private interface to test conflict handling.
        assert bulk._docs is not None
        bulk._docs.append(foo)

    assert bulk.response is not None
    assert len(bulk.response) == 2

    assert "ok" in bulk.response[0]
    assert "error" in bulk.response[1]
    assert bulk.response[1]["error"] == "conflict"

    keys = [key async for key in database.akeys()]

    assert len(keys) == 1
    assert sorted(keys) == ["foo"]


async def test_create_docs_mixed(database: Database) -> None:
    async with database.create_docs(["foo"]) as bulk:
        bulk.create("baz")

    assert bulk.response is not None
    assert len(bulk.response) == 2

    keys = [key async for key in database.akeys()]

    assert len(keys) == 2
    assert sorted(keys) == ["baz", "foo"]


async def test_create_docs_for_existing(filled_database: Database) -> None:
    async with filled_database.create_docs(["new", "foo"]) as bulk:
        bulk.create("baz")

    assert bulk.response is not None
    assert bulk.error is not None
    assert bulk.ok is not None

    assert len(bulk.response) == 3
    assert len(bulk.ok) == 1
    assert len(bulk.error) == 2
    assert bulk.response[1]["error"] == "conflict"
    assert bulk.response[2]["error"] == "conflict"


async def test_update_external_documents(filled_database: Database) -> None:
    foo = await filled_database.get("foo")

    assert "zebras" not in foo

    async with filled_database.update_docs() as bulk:
        foo["zebras"] = "awesome 🦓"
        bulk.append(foo)

        with pytest.raises(ValueError):
            bulk.append(foo)

    foo = await filled_database.get("foo")
    assert foo["zebras"] == "awesome 🦓"


async def test_no_bulk_request_on_exception(database: Database, doc: Document) -> None:
    from aiocouch.bulk import BulkOperation

    doc["zebras"] = "awesome 🦓"

    with pytest.raises(Exception):
        async with BulkOperation(database=database) as bulk:
            bulk.append(doc)

            # simulate an error
            raise Exception()

    assert bulk.error is None
    assert bulk.ok is None
    assert bulk.response is None

    # check that the changes were not send to the server
    doc2 = await database.create(doc.id)
    assert "zebras" not in doc2


async def test_bulk_get(filled_database: Database) -> None:
    response = await filled_database._bulk_get(
        [{"id": id} for id in ["foo", "foo2", "baz", "baz2", "bar"]]
    )

    results = response["results"]

    assert len(results) == 5

    assert results[0]["id"] == "foo"
    assert "ok" in results[0]["docs"][0]

    assert results[1]["id"] == "foo2"
    assert "ok" in results[1]["docs"][0]

    assert results[2]["id"] == "baz"
    assert "ok" in results[2]["docs"][0]

    assert results[3]["id"] == "baz2"
    assert "ok" in results[3]["docs"][0]

    assert results[4]["id"] == "bar"
    assert "error" in results[4]["docs"][0]
