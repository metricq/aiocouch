import pytest


# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_list_databases(event_loop, couchdb):
    dbs = await couchdb.list_databases()

    assert "aiocouch_test_fixture_database" not in dbs


async def test_list_database(event_loop, couchdb, database):

    dbs = await couchdb.list_databases()
    assert "aiocouch_test_fixture_database" in dbs


async def test_database_cache(couchdb, database):
    assert database == await couchdb.get_database("aiocouch_test_fixture_database")


async def test_create_delete_database(event_loop, couchdb):
    database = await couchdb.get_database("aiocouch_test_fixture_database2")

    dbs = await couchdb.list_databases()
    assert "aiocouch_test_fixture_database2" in dbs

    await database.delete()

    dbs = await couchdb.list_databases()
    assert "aiocouch_test_fixture_database2" not in dbs
