from typing import Any, cast

import pytest

from aiocouch import ConflictError, NotFoundError
from aiocouch.database import Database
from aiocouch.document import Document

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_constructor(database: Database) -> None:
    from aiocouch.document import Document

    doc = Document(database, "foo", data={"foo": 42})

    assert doc.id == "foo"
    assert doc["_id"] == "foo"
    assert doc["foo"] == 42


async def test_constructor_with_wrong_type_for_data(
    database: Database, doc: Document
) -> None:
    with pytest.raises(TypeError):
        Document(database, "foo", data=cast(Any, 42))

    with pytest.raises(TypeError):
        Document(database, "foo", data=cast(Any, doc))


async def test_context_manager_by_creating_new_doc(database: Database) -> None:
    from aiocouch.document import Document

    new_doc_id = "new_doc"

    # Use context manager to create & save new doc with some data in it
    async with Document(database=database, id=new_doc_id) as document:
        assert (len(document.keys())) == 1
        assert document["_id"] == document.id == new_doc_id
        document["king"] = "elvis"

    # Verify whether the data was actually written to the server or not
    saved_doc = await database.get(new_doc_id)

    assert saved_doc["_id"] == saved_doc.id == new_doc_id
    assert saved_doc.rev is not None
    assert saved_doc.rev.startswith("1-")
    assert "king" in saved_doc
    assert saved_doc["king"] == "elvis"


async def test_context_manager_by_retrieving_existing_doc(
    filled_database: Database,
) -> None:
    """Test async context manager by retrieving an existing doc from
    filled_database fixture & verify that data was actually written to server"""

    from aiocouch.document import Document

    async with Document(database=filled_database, id="foo") as document:
        doc_keys = document.keys()
        assert len(doc_keys) == 4
        assert document["_id"] == document.id == "foo"
        assert document["_rev"] == document.rev
        assert "bar" in doc_keys
        assert document["bar"] is True
        assert document["bar2"] == 3


async def test_context_manager_with_data_parameter(database: Database) -> None:
    from aiocouch.document import Document

    new_doc_id = "new_doc"

    doc_data = {"king": "elvis"}

    # Create and save a new document with the data given to data parameter
    async with Document(database=database, id=new_doc_id, data=doc_data) as document:
        assert (len(document.keys())) == 2
        assert document.rev is None
        assert document["_id"] == document.id == new_doc_id
        assert "king" in document
        assert document["king"] == "elvis"

    # Verify that the data was actually written to server by context manager
    saved_doc = await database.get(new_doc_id)

    assert saved_doc["_id"] == saved_doc.id == new_doc_id
    assert saved_doc.rev is not None
    assert saved_doc.rev.startswith("1-")
    assert "king" in saved_doc
    assert saved_doc["king"] == "elvis"


async def test_save(database: Database) -> None:
    doc = await database.create("foo42")
    doc["bar"] = True
    await doc.save()

    keys = [key async for key in database.akeys()]

    assert "foo42" in keys
    assert len(keys) == 1


async def test_dict_from_doc(filled_database: Database) -> None:
    doc = await filled_database["foo"]

    doc_as_dict = doc.data
    assert isinstance(doc_as_dict, dict)

    doc = Document(filled_database, "buzz")
    doc_as_dict = doc.data
    assert doc_as_dict is None

    await doc.save()
    doc_as_dict = doc.data
    assert isinstance(doc_as_dict, dict)


async def test_fetch_clean_document(filled_database: Database) -> None:
    from aiocouch.document import Document

    doc = Document(filled_database, "foo")
    await doc.fetch()


async def test_fetch_dirty_document(database: Database) -> None:
    from aiocouch import ConflictError

    doc = await database.create("foo")

    doc["dirty"] = "shitz"
    with pytest.raises(ConflictError):
        await doc.fetch()


async def test_save_with_data(database: Database) -> None:
    doc = await database.create("foo")

    doc["blub"] = "blubber"

    await doc.save()

    assert doc["_id"] == doc.id == "foo"
    assert doc.rev is not None
    assert doc.rev.startswith("1-")
    assert doc._dirty_cache is False

    doc = await database["foo"]
    assert doc["_id"] == doc.id == "foo"
    assert doc.rev is not None
    assert doc.rev.startswith("1-")
    assert doc["blub"] == "blubber"
    assert doc._dirty_cache is False


async def test_conflict(filled_database: Database) -> None:
    doc1 = await filled_database["foo"]
    doc2 = await filled_database["foo"]

    doc1["blub"] = "new"
    await doc1.save()

    doc2["blub"] = "bar"

    with pytest.raises(ConflictError):
        await doc2.save()


async def test_conflict_without_rev(database: Database) -> None:
    doc1 = await database.create("fou")
    doc2 = await database.create("fou")

    assert doc1.rev is None

    doc1["blub"] = "new"
    await doc1.save()

    assert doc1.rev is not None
    assert doc1.rev.startswith("1-")
    assert doc2.rev is None

    doc2["blub"] = "bar"

    with pytest.raises(ConflictError):
        await doc2.save()

    assert doc2.rev is None


async def test_override_conflict(database: Database) -> None:
    doc1 = await database.create("fou")
    doc2 = await database.create("fou")

    doc1["blub"] = "new"
    await doc1.save()

    doc2["blub"] = "bar"

    try:
        await doc2.save()
        assert False
    except ConflictError:
        doc2.rev = doc1.rev
        await doc2.save()

    doc3 = await database["fou"]
    assert doc3.rev is not None
    assert doc3.rev.startswith("2-")
    assert doc3["blub"] == "bar"


async def test_update(filled_database: Database) -> None:
    doc = await filled_database["foo"]

    assert doc.rev == doc["_rev"]
    assert doc.rev.startswith("1-")
    assert doc._dirty_cache is False

    del doc["bar"]
    doc["blub"] = "blubber"

    assert doc["_rev"] == doc.rev
    assert doc["_rev"].startswith("1-")
    assert doc._dirty_cache is True

    await doc.save()

    assert doc["_id"] == doc.id == "foo"
    assert doc["_rev"] == doc.rev
    assert doc["_rev"].startswith("2-")
    assert doc._dirty_cache is False

    doc = await filled_database["foo"]
    assert doc["_id"] == doc.id == "foo"
    assert doc["_rev"].startswith("2-")
    assert doc["_rev"] == doc.rev
    assert doc._dirty_cache is False
    assert doc["blub"] == "blubber"
    assert "bar" not in doc


async def test_delete(filled_database: Database) -> None:
    doc = await filled_database["foo"]

    await doc.delete()

    keys = [key async for key in filled_database.akeys()]

    assert len(keys) == 3
    assert sorted(keys) == ["baz", "baz2", "foo2"]


async def test_delete_dirty(filled_database: Database) -> None:
    from aiocouch import ConflictError

    doc = await filled_database["foo"]

    doc["fuzzy"] = "lizzy"

    with pytest.raises(ConflictError):
        await doc.delete()

    assert doc.rev
    assert doc.rev.startswith("1-")


async def test_safe_deleted(filled_database: Database) -> None:
    doc = await filled_database["foo"]

    assert doc.rev
    assert doc.rev.startswith("1-")

    await doc.delete()

    assert doc.rev
    assert doc.rev.startswith("2-")

    doc["Zebras"] = "are majestic"
    await doc.save()

    assert doc.rev
    assert doc.rev.startswith("3-")


async def test_copy(filled_database: Database) -> None:
    foo = await filled_database["foo"]
    assert foo.data is not None

    foo_copy = await foo.copy("foo_copy")

    assert foo_copy.data is not None
    assert foo_copy.data.keys() == foo.data.keys()
    for key in foo_copy.data.keys():
        if key == "_id":
            continue
        assert foo_copy[key] == foo[key]


async def test_get_info(database: Database) -> None:
    doc = await database.create("foo42")
    await doc.save()

    info = await doc.info()
    assert info["ok"]
    assert info["id"] == "foo42"
    assert info["rev"].startswith("1-")

    doc["bar"] = True
    await doc.save()

    info = await doc.info()
    assert info["ok"]
    assert info["id"] == "foo42"
    assert info["rev"].startswith("2-")

    await doc.delete()

    with pytest.raises(NotFoundError):
        await doc.info()


async def test_rev(doc: Document) -> None:
    assert doc.rev is None
    await doc.save()
    assert doc.rev is not None

    rev = doc.rev
    assert rev.startswith("1-")
    with pytest.raises(TypeError):
        doc.rev = 42
    assert doc.rev == rev


async def test_doc_update(doc: Document) -> None:
    assert "test" not in doc

    doc.update({"test": "value"})

    assert "test" in doc
    assert doc["test"] == "value"


async def test_doc_items_keys_values(doc: Document) -> None:
    assert list(doc.keys()) == ["_id"]
    assert list(doc.values()) == ["foo"]
    assert dict(doc.items()) == {"_id": "foo"}


async def test_filled_doc_items_keys_values(doc: Document) -> None:
    doc.update({"test": "value"})

    assert list(doc.keys()) == ["_id", "test"]
    assert list(doc.values()) == ["foo", "value"]
    assert dict(doc.items()) == {"_id": "foo", "test": "value"}


async def test_get(doc: Document) -> None:
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


async def test_repr(doc: Document) -> None:
    print(doc)


async def test_cache(doc: Document) -> None:
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


async def test_fetch_rev(filled_database: Database) -> None:
    doc = await filled_database.get("foo")
    old_rev = doc.rev

    doc["Zebras"] = "are the best"
    await doc.save()

    assert doc.rev != old_rev

    await doc.fetch(rev=old_rev)

    assert doc.rev == old_rev
    assert "Zebras" not in doc

    doc2 = await filled_database.get("foo", rev=old_rev)
    assert doc.data == doc2.data


async def test_data_len(doc: Document, saved_doc: Document) -> None:
    assert doc.data is None
    assert len(doc) == 1

    assert saved_doc.data
    assert len(saved_doc.data) == 1
    assert len(saved_doc) == 3

    doc2 = Document(cast(Database, None), "doc2", {"foo": "bar"})
    assert doc2.data is None
    assert len(doc2) == 2

    doc3 = Document(cast(Database, None), "doc3")
    assert doc3.data is None
    assert len(doc3) == 1


async def test_clear_with_empty_doc(doc: Document) -> None:
    id = doc.id
    doc.clear()
    assert doc.id == id
    assert doc.data is None
    assert len(doc) == 1


async def test_clear_with_rev(saved_doc: Document) -> None:
    id = saved_doc.id
    saved_doc.clear()
    assert saved_doc.id == id
    assert saved_doc.data == {}
    assert len(saved_doc) == 2


async def test_clear_without_rev() -> None:
    doc = Document(cast(Database, None), "doc", {"foo": "bar"})
    id = doc.id
    doc.clear()
    assert doc.id == id
    assert doc.data is None
    assert len(doc) == 1


async def test_data_of_deleted_doc(saved_doc: Document) -> None:
    await saved_doc.delete()

    assert saved_doc.data is None


async def test_data_of_empty_doc(doc: Document) -> None:
    await doc.save()

    assert doc.id
    assert doc.rev
    assert len(doc) == 2

    assert doc.data is not None
    assert doc.data == {}


async def test_deleted_document_data(saved_doc: Document) -> None:
    await saved_doc.delete()

    assert saved_doc.data is None
    assert "_deleted" in saved_doc


async def test_security_document_context_manager(database: Database) -> None:
    from aiocouch.document import SecurityDocument

    async with SecurityDocument(database=database) as sec_doc:
        assert sec_doc.members is None
        assert sec_doc.admins is None

        assert sec_doc.member_roles is None or sec_doc.member_roles == ["_admin"]
        assert sec_doc.admin_roles is None or sec_doc.admin_roles == ["_admin"]

        sec_doc.add_member("lennon")
        sec_doc.add_admin("elvis")

    async with SecurityDocument(database=database) as sec_doc:
        assert sec_doc.members is not None
        assert "lennon" in sec_doc.members

        assert sec_doc.admins is not None
        assert "elvis" in sec_doc.admins

        sec_doc.remove_member(member="lennon")
        sec_doc.remove_admin(admin="elvis")

    async with SecurityDocument(database=database) as sec_doc:
        assert sec_doc.members is not None
        assert "lennon" not in sec_doc.members

        assert sec_doc.admins is not None
        assert "elvis" not in sec_doc.admins
