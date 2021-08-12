from aiocouch.bulk import BulkOperation
import pytest

from aiocouch.document import Document
from aiocouch.database import Database

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
    async with database.update_docs(["foo", "baz"], create=True) as docs:
        async for doc in docs:
            doc["llama"] = "awesome"

    keys = [key async for key in database.akeys()]

    assert len(keys) == 2
    assert sorted(keys) == ["baz", "foo"]

    async for doc in database.values():
        assert "llama" in doc
        assert doc["llama"] == "awesome"


async def test_update_docs_no_change(filled_database: Database) -> None:
    async with filled_database.update_docs(["foo", "baz"]) as docs:
        pass

    assert docs.status == []


async def test_update_dont_crash_on_pristine_doc(filled_database: Database) -> None:
    doc = await filled_database["foo"]
    doc["llama"] = "awesome"
    await doc.save()

    async with filled_database.update_docs(["foo", "baz"], create=True) as docs:
        async for doc in docs:
            doc["llama"] = "awesome"


async def test_update_docs_for_deleted(filled_database: Database) -> None:
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


async def test_update_docs_for_errored(filled_database: Database) -> None:
    doc = await filled_database["foo"]
    doc["something"] = 42
    async with filled_database.update_docs(["foo", "baz"]) as docs:
        # provoke a conflict for document foo
        await doc.save()

        async for doc in docs:
            doc["thing"] = 42

    assert docs.status is not None
    assert len(docs.status) == 2

    assert docs.ok is not None
    assert len(docs.ok) == 1
    doc_ok = docs.ok[0]
    assert doc_ok.id == "baz"
    assert doc_ok["thing"] == 42
    assert doc_ok["_rev"].startswith("2-")

    assert docs.error is not None
    assert len(docs.error) == 1
    doc_err = docs.error[0]
    assert doc_err.id == "foo"
    assert doc_err["_rev"].startswith("1-")
    assert "something" not in doc_err


async def test_create_docs_with_ids(database: Database) -> None:
    async with database.create_docs(["foo", "baz"]) as docs:
        pass

    assert docs.status is not None
    assert len(docs.status) == 2

    keys = [key async for key in database.akeys()]

    assert len(keys) == 2
    assert sorted(keys) == ["baz", "foo"]


async def test_create_docs_with_create(database: Database) -> None:
    async with database.create_docs() as docs:
        docs.create("foo", data={"counter": 42})
        docs.create("baz")

        with pytest.raises(ValueError):
            docs.create("foo")

    assert docs.status is not None
    assert len(docs.status) == 2

    keys = [key async for key in database.akeys()]

    assert len(keys) == 2
    assert sorted(keys) == ["baz", "foo"]

    foo = await database["foo"]
    assert "counter" in foo
    assert foo["counter"] == 42


async def test_create_docs_with_create_duplicate(database: Database) -> None:
    async with database.create_docs() as docs:
        foo = docs.create("foo")

        # DO NOT DO THIS! This is just using the private interface to test conflict handling.
        assert docs._docs is not None
        docs._docs.append(foo)

    assert docs.status is not None
    assert len(docs.status) == 2

    assert "ok" in docs.status[0]
    assert "error" in docs.status[1]
    assert docs.status[1]["error"] == "conflict"

    keys = [key async for key in database.akeys()]

    assert len(keys) == 1
    assert sorted(keys) == ["foo"]


async def test_create_docs_mixed(database: Database) -> None:
    async with database.create_docs(["foo"]) as docs:
        docs.create("baz")

    assert docs.status is not None
    assert len(docs.status) == 2

    keys = [key async for key in database.akeys()]

    assert len(keys) == 2
    assert sorted(keys) == ["baz", "foo"]


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
        async with BulkOperation(database=database) as docs:
            docs.append(doc)

            # simulate an error
            raise Exception()

    assert docs.error == None
    assert docs.ok == None
    assert docs.status == None

    # check that the changes were not send to the server
    doc2 = await database.create(doc.id)
    assert "zebras" not in doc2