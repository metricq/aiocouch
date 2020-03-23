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


async def test_getitem_for_existing(filled_database):
    doc = await filled_database["foo"]

    assert doc["bar"] is True
    assert doc["_id"] == doc.id == "foo"
    assert doc["_rev"].startswith("1-")
    assert doc._dirty_cache is False


async def test_getitem_for_non_existing(database):
    with pytest.raises(KeyError):
        await database["foo"]


async def test_create_for_existing(filled_database):
    with pytest.raises(KeyError):
        await filled_database.create("foo")


async def test_create_for_existing_exists_true(filled_database):
    doc = await filled_database.create("foo", exists_ok=True)

    assert doc["bar"] is True
    assert doc["_id"] == doc.id == "foo"
    assert doc["_rev"].startswith("1-")
    assert doc._dirty_cache is False


async def test_get_for_existing(filled_database):
    doc = await filled_database.get("foo")

    assert doc["bar"] is True
    assert doc["_id"] == doc.id == "foo"
    assert doc["_rev"].startswith("1-")
    assert doc._dirty_cache is False


async def test_get_for_non_existing(database):
    with pytest.raises(KeyError):
        await database.get("foo")


async def test_get_for_non_existing_with_empty_default(database):
    doc = await database.get("foo", default={})

    assert doc["_id"] == doc.id == "foo"
    assert "_rev" not in doc
    assert doc._dirty_cache is True


async def test_get_for_non_existing_with_default(database):
    doc = await database.get("foo", default={"jumbo": "dumbo", "value": 42})

    assert doc["_id"] == doc.id == "foo"
    assert "_rev" not in doc
    assert doc["jumbo"] == "dumbo"
    assert doc["value"] == 42
    assert doc._dirty_cache is True


async def test_akeys_with_prefix(filled_database):
    keys = [key async for key in filled_database.akeys(prefix="ba")]

    assert len(keys) == 2
    assert (sorted(keys)) == ["baz", "baz2"]


async def test_akeys_with_keys(filled_database):
    keys = [
        key async for key in filled_database.akeys(keys=["foo", "baz", "halloween"])
    ]

    assert len(keys) == 2
    assert keys == ["foo", "baz"]


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


async def test_update_docs_no_change(filled_database):
    async with filled_database.update_docs(["foo", "baz"]) as docs:
        pass

    assert docs.status == []


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

    assert len(keys) == 2
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
    matching_docs = [doc async for doc in filled_database.find({"bar": True})]

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
    matching_docs = [doc async for doc in filled_database.find({"bar": True}, limit=1)]

    assert len(matching_docs) == 1

    from aiocouch.document import Document

    matching_keys = []
    for doc in matching_docs:
        assert isinstance(doc, Document)
        matching_keys.append(doc.id)

    assert "baz2" in matching_keys


async def test_find_invalid_selector(database):
    with pytest.raises(ValueError):
        [
            doc
            async for doc in database.find({"bar": True, "fields": "anything"}, limit=1)
        ]


async def test_alldocs_values(filled_database):
    values = [key async for key, value in filled_database.all_docs.aitems()]

    assert len(values) == 4

    assert values[0] == "baz"
    assert values[1] == "baz2"
    assert values[2] == "foo"
    assert values[3] == "foo2"


async def test_values_for_filled(filled_database):
    keys = [doc.id async for doc in filled_database.values()]

    assert len(keys) == 4
    assert sorted(keys) == ["baz", "baz2", "foo", "foo2"]


async def test_values_for_filled_limited(filled_database):
    keys = [doc.id async for doc in filled_database.values(limit=1)]

    assert len(keys) == 1
    assert keys == ["baz"]


async def test_many_docs(large_filled_database):
    keys = [key async for key in large_filled_database.akeys()]
    assert len(keys) == 2000

    docs = [doc async for doc in large_filled_database.docs()]
    assert len(docs) == 2000

    find_docs = [
        doc async for doc in large_filled_database.find(selector={"llama": "awesome"})
    ]
    assert len(find_docs) == 2000


async def test_get_design_doc(filled_database_with_view):
    await filled_database_with_view.design_doc("test_ddoc2")
    await filled_database_with_view.design_doc("test_ddoc", exists_ok=True)

    with pytest.raises(KeyError):
        await filled_database_with_view.design_doc("test_ddoc")


async def test_set_invalid_design_doc_key(filled_database_with_view):
    ddoc = await filled_database_with_view.design_doc("test_ddoc", exists_ok=True)

    with pytest.raises(KeyError):
        ddoc["foo"] = "bar"


async def test_get_security(database):
    sec = await database.security()

    assert sec.members is None
    assert sec.admins is None

    assert sec.member_roles is None
    assert sec.admin_roles is None


async def test_security_add_members(database):
    sec = await database.security()
    sec.add_member("foobert")

    await sec.save()

    sec2 = await database.security()
    assert "foobert" in sec2.members

    sec2.remove_member("foobert")
    await sec2.save()

    sec3 = await database.security()
    assert "foobert" not in sec3.members


async def test_security_remove_member(database):
    sec = await database.security()
    with pytest.raises(KeyError):
        sec.remove_member("foobert")


async def test_security_add_admins(database):
    sec = await database.security()
    sec.add_admin("foobert")

    await sec.save()

    sec2 = await database.security()
    assert "foobert" in sec2.admins

    sec2.remove_admin("foobert")
    await sec2.save()

    sec3 = await database.security()
    assert "foobert" not in sec3.admins


async def test_security_remove_admin(database):
    sec = await database.security()
    with pytest.raises(KeyError):
        sec.remove_admin("foobert")


async def test_security_stays_empty(database):
    sec = await database.security()
    await sec.save()

    sec2 = await database.security()
    assert sec2._data == {}
