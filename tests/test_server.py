from aiocouch import CouchDB, Database

import pytest


# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_list_databases(couchdb: CouchDB) -> None:
    dbs = await couchdb.keys()
    assert "aiocouch_test_fixture_database" not in dbs


async def test_list_database(couchdb: CouchDB, database: Database) -> None:
    dbs = await couchdb.keys()
    assert "aiocouch_test_fixture_database" in dbs


async def test_create_delete_database(couchdb: CouchDB) -> None:
    database = await couchdb.create("aiocouch_test_fixture_database2")

    dbs = await couchdb.keys()
    assert "aiocouch_test_fixture_database2" in dbs

    await database.delete()

    dbs = await couchdb.keys()
    assert "aiocouch_test_fixture_database2" not in dbs


async def test_create_for_existing(couchdb: CouchDB, database: Database) -> None:
    from aiocouch import PreconditionFailedError

    with pytest.raises(PreconditionFailedError):
        await couchdb.create(database.id)


async def test_create_for_existing_ok(couchdb: CouchDB, database: Database) -> None:
    await couchdb.create(database.id, exists_ok=True)


async def test_get_for_existing(couchdb: CouchDB, database: Database) -> None:
    await couchdb[database.id]


async def test_get_for_non_existing(couchdb: CouchDB, database: Database) -> None:
    from aiocouch import NotFoundError

    with pytest.raises(NotFoundError):
        await couchdb[database.id + "not_existing"]


async def test_get_info(couchdb: CouchDB) -> None:
    await couchdb.info()


async def test_get_database_info(database: Database) -> None:
    await database.info()
