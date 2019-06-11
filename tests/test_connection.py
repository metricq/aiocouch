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
        user = "admin"

    assert user == response["userCtx"]["name"]


async def test_with(event_loop):
    from aiocouch.remote import RemoteServer
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

    async with RemoteServer(hostname, user=user, password=password):
        pass
