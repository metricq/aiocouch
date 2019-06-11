import pytest


@pytest.fixture
async def couchdb():
    from aiocouch import CouchDB
    import os

    try:
        hostname = os.environ["COUCHDB_HOST"]
    except KeyError:
        hostname = "http://localhost:5984"

    try:
        user = os.environ["COUCHDB_USER"]
    except KeyError:
        user = "admin"

    try:
        password = os.environ["COUCHDB_PASS"]
    except KeyError:
        password = "admin"

    async with CouchDB(hostname, user=user, password=password) as couchdb:
        yield couchdb


@pytest.fixture
async def database(couchdb):
    database = await couchdb.get_database("aiocouch_test_fixture_database")

    yield database

    await database.delete()


@pytest.fixture
async def filled_database(database):
    doc = await database.get("foo")
    doc["bar"] = True

    doc = await database.get("foo2")
    doc["bar"] = True

    doc = await database.get("baz")
    doc["bar"] = False

    doc = await database.get("baz2")
    doc["bar"] = True

    await database.save_all()

    yield database
