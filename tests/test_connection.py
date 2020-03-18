import os

import pytest

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_server_version(event_loop, couchdb):
    response = await couchdb._server._get("/")

    from packaging import version

    assert version.parse("2.0.0") < version.parse(response["version"])


async def test_session(event_loop, couchdb):
    response = await couchdb._server._get("/_session")

    assert "ok" in response
    assert "userCtx" in response
    assert "name" in response["userCtx"]

    try:
        user = os.environ["COUCHDB_USER"]
    except KeyError:
        user = None

    assert user == response["userCtx"]["name"]


async def test_cookie_authentication(event_loop, couchdb_user):
    from aiocouch import CouchDB

    import aiohttp

    import os

    try:
        hostname = os.environ["COUCHDB_HOST"]
    except KeyError:
        hostname = "http://localhost:5984"

    user = "aiocouch_test_user"

    # create a session cookie, which can be used later
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{hostname}/_session", data={"name": user, "password": user},
        ) as resp:
            assert resp.status == 200
            await resp.json()
            cookie = resp.cookies["AuthSession"].value

    async with CouchDB(hostname, cookie=cookie) as couchdb:
        await couchdb.check_credentials()

        response = await couchdb._server._get("/_session")

        assert user == response["userCtx"]["name"]


async def test_basic_authentication(event_loop):
    from aiocouch import CouchDB
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

    async with CouchDB(hostname, user=user, password=password) as couchdb:
        await couchdb.check_credentials()


async def test_with_wrong_credentials(event_loop):
    from aiocouch import CouchDB
    from aiocouch import UnauthorizedError

    import os

    try:
        hostname = os.environ["COUCHDB_HOST"]
    except KeyError:
        hostname = "http://localhost:5984"

    with pytest.raises(UnauthorizedError):
        async with CouchDB(
            hostname,
            user="invalid",
            password="rcvy438tyb7est0fb38s4tybf74etbc7843tybfs4fb7v49bstf68bs495ftb63948ft5b9s6",
        ) as couchdb:
            await couchdb["does_not_exist"]


async def test_check_wrong_credentials(event_loop):
    from aiocouch import CouchDB
    from aiocouch import UnauthorizedError

    import os

    try:
        hostname = os.environ["COUCHDB_HOST"]
    except KeyError:
        hostname = "http://localhost:5984"

    with pytest.raises(UnauthorizedError):
        async with CouchDB(
            hostname,
            user="invalid",
            password="rcvy438tyb7est0fb38s4tybf74etbc7843tybfs4fb7v49bstf68bs495ftb63948ft5b9s6",
        ) as couchdb:
            await couchdb.check_credentials()
