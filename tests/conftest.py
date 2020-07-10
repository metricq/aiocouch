import pytest


@pytest.fixture
async def couchdb_user_account(couchdb):
    users = await couchdb.create("_users", exists_ok=True)

    doc = await users.create("org.couchdb.user:aiocouch_test_user")
    doc["name"] = "aiocouch_test_user"
    doc["password"] = "aiocouch_test_user"
    doc["roles"] = ["aiocouch_test_role"]
    doc["type"] = "user"

    await doc.save()
    assert doc["_id"] == "org.couchdb.user:aiocouch_test_user"
    assert doc.id == "org.couchdb.user:aiocouch_test_user"

    yield couchdb

    await doc.delete()


@pytest.fixture
async def couchdb(event_loop):
    from aiocouch import CouchDB
    import asyncio
    import os

    try:
        hostname = os.environ["COUCHDB_HOST"]
    except KeyError:
        hostname = "http://localhost:5984"

    try:
        user = os.environ["COUCHDB_USER"]
    except KeyError:
        user = None

    try:
        password = os.environ["COUCHDB_PASS"]
    except KeyError:
        password = ""

    async with CouchDB(
        hostname, user=user, password=password, loop=event_loop
    ) as couchdb:
        yield couchdb

    # Give the couchdb server some time, so the assumptions of an empty database isn't
    # broken for subsequent tests. This delay used to be part of the disconnect
    # procedure, but #6 removed that. Therefore, we do sleep for the previous amount
    # here. This should give the server some time to delete the old fixtures.
    await asyncio.sleep(0.250)


@pytest.fixture
async def couchdb_with_user_access(couchdb_user_account):
    from aiocouch import CouchDB
    import os

    try:
        hostname = os.environ["COUCHDB_HOST"]
    except KeyError:
        hostname = "http://localhost:5984"

    async with CouchDB(
        hostname, user="aiocouch_test_user", password="aiocouch_test_user"
    ) as couchdb:
        yield couchdb


@pytest.fixture
async def database(couchdb):
    database = await couchdb.create("aiocouch_test_fixture_database")

    yield database

    await database.delete()


@pytest.fixture
async def filled_database(database):
    doc = await database.create("foo")
    doc["bar"] = True
    await doc.save()

    doc = await database.create("foo2")
    doc["bar"] = True
    await doc.save()

    doc = await database.create("baz")
    doc["bar"] = False
    await doc.save()

    doc = await database.create("baz2")
    doc["bar"] = True
    await doc.save()

    yield database


@pytest.fixture
async def filled_database_with_view(filled_database):
    ddoc = await filled_database.design_doc("test_ddoc")
    await ddoc.create_view("null_view", "function (doc) { emit(doc._id, null); }")
    await ddoc.create_view("full_view", "function (doc) { emit(doc._id, doc); }")
    await ddoc.create_view("bar_view", "function (doc) { emit(doc._id, doc.bar); }")

    yield filled_database


@pytest.fixture
async def large_filled_database(database):
    async with database.update_docs(
        [f"doc{i}" for i in range(2000)], create=True
    ) as docs:
        async for doc in docs:
            doc["llama"] = "awesome"

    yield database


@pytest.fixture
async def doc(database):
    doc = await database.create("foo")
    yield doc
