import pytest


# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_list_databases(event_loop, couchdb):
    dbs = await couchdb.keys()

    assert "aiocouch_test_fixture_database" not in dbs


async def test_list_database(event_loop, couchdb, database):

    dbs = await couchdb.keys()
    assert "aiocouch_test_fixture_database" in dbs


async def test_create_delete_database(event_loop, couchdb):
    database = await couchdb.create("aiocouch_test_fixture_database2")

    dbs = await couchdb.keys()
    assert "aiocouch_test_fixture_database2" in dbs

    await database.delete()

    dbs = await couchdb.keys()
    assert "aiocouch_test_fixture_database2" not in dbs


async def test_create_for_existing(couchdb, database):
    with pytest.raises(KeyError):
        await couchdb.create(database.id)


async def test_create_for_existing_ok(couchdb, database):
    await couchdb.create(database.id, exists_ok=True)


async def test_get_for_existing(couchdb, database):
    await couchdb[database.id]


async def test_get_for_non_existing(couchdb, database):
    with pytest.raises(KeyError):
        await couchdb[database.id + "not_existing"]


async def test_get_info(couchdb):
    await couchdb.info()


async def test_get_database_info(database):
    await database.info()
