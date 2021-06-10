import os
from contextlib import suppress
from typing import Optional

import pytest

from aiocouch import CouchDB

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_server_version(couchdb: CouchDB) -> None:
    response = await couchdb.info()

    from packaging import version

    assert version.parse("2.0.0") < version.parse(response["version"])


async def test_session(couchdb: CouchDB) -> None:
    headers, response = await couchdb._server._get("/_session")

    assert not isinstance(response, bytes)

    assert "ok" in response
    assert "userCtx" in response
    assert "name" in response["userCtx"]

    user: Optional[str] = None

    with suppress(KeyError):
        user = os.environ["COUCHDB_USER"]

    assert user == response["userCtx"]["name"]


async def test_cookie_authentication(couchdb_with_user_access: CouchDB) -> None:
    import os

    import aiohttp

    from aiocouch import CouchDB

    try:
        hostname = os.environ["COUCHDB_HOST"]
    except KeyError:
        hostname = "http://localhost:5984"

    user = "aiocouch_test_user"

    # create a session cookie, which can be used later
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{hostname}/_session",
            data={"name": user, "password": user},
        ) as resp:
            assert resp.status == 200
            await resp.json()
            cookie = resp.cookies["AuthSession"].value

    async with CouchDB(hostname, cookie=cookie) as couchdb:
        await couchdb.check_credentials()

        headers, response = await couchdb._server._get("/_session")
        assert not isinstance(response, bytes)
        assert user == response["userCtx"]["name"]


async def test_basic_authentication() -> None:
    import os

    from aiocouch import CouchDB

    try:
        hostname = os.environ["COUCHDB_HOST"]
    except KeyError:
        hostname = "http://localhost:5984"

    user: Optional[str] = None
    with suppress(KeyError):
        user = os.environ["COUCHDB_USER"]

    try:
        password = os.environ["COUCHDB_PASS"]
    except KeyError:
        password = ""

    async with CouchDB(hostname, user=user, password=password) as couchdb:
        await couchdb.check_credentials()


async def test_with_wrong_credentials() -> None:
    import os

    from aiocouch import CouchDB, UnauthorizedError

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


async def test_check_wrong_credentials() -> None:
    import os

    from aiocouch import CouchDB, UnauthorizedError

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
