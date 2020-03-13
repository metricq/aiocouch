# Copyright (c) 2019, ZIH,
# Technische Universitaet Dresden,
# Federal Republic of Germany
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.
#     * Neither the name of metricq nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from .exception import raises

import asyncio
import aiohttp

from urllib.parse import quote


def _quote_id(id):
    return quote(id, safe=[])


def _stringify_params(params):
    if params is None:
        return None
    result = {}
    for key, value in params.items():
        if value is None:
            continue
        elif value is True:
            value = "true"
        elif value is False:
            value = "false"

        result[key] = value

    return result


class RemoteServer(object):
    def __init__(self, server, user=None, password=None, cookie=None, **kwargs):
        self._server = server
        auth = aiohttp.BasicAuth(user, password) if user else None
        headers = {"Cookie": "AuthSession=" + cookie} if cookie else None
        self._http_session = aiohttp.ClientSession(headers=headers, auth=auth, **kwargs)
        self._databases = {}

    async def __aenter__(self):
        await self._check_session()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    async def _get(self, path, params=None):
        return await self._request("GET", path, params=params)

    async def _put(self, path, data=None, params=None):
        return await self._request("PUT", path, json=data, params=params)

    async def _post(self, path, data, params=None):
        return await self._request("POST", path, json=data, params=params)

    async def _delete(self, path, params=None):
        return await self._request("DELETE", path, params=params)

    async def _head(self, path, params=None):
        return await self._request("HEAD", path, params=params)

    async def _request(self, method, path, params, **kwargs):
        kwargs["params"] = _stringify_params(params)

        async with self._http_session.request(
            method, url=f"{self._server}{path}", **kwargs
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _all_dbs(self, **params):
        return await self._get("/_all_dbs", params)

    async def close(self):
        await self._http_session.close()
        await asyncio.sleep(0.250)

    @raises(401, "Authentification failed, check provided credentials.")
    async def _check_session(self):
        await self._get("/_session")


class RemoteDatabase(object):
    def __init__(self, remote, id):
        self.id = id
        self._remote = remote

    @property
    def endpoint(self):
        return f"/{_quote_id(self.id)}"

    async def _exists(self):
        try:
            await self._remote._head(self.endpoint)
            return True
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                return False
            else:
                raise e

    @raises(404, "Requested database not found ({id})")
    async def _get(self):
        return await self._remote._get(self.endpoint)

    @raises(400, "Invalid database name")
    @raises(401, "CouchDB Server Administrator privileges required")
    @raises(412, "Database already exists")
    async def _put(self, **params):
        return await self._remote._put(self.endpoint)

    @raises(400, "Invalid database name or forgotten document id by accident")
    @raises(401, "CouchDB Server Administrator privileges required")
    @raises(404, "Database doesn’t exist or invalid database name ({id})")
    async def _delete(self):
        await self._remote._delete(self.endpoint)

    @raises(400, "The request provided invalid JSON data or invalid query parameter")
    @raises(401, "Read permission required")
    @raises(404, "Invalid database name")
    @raises(415, "Bad Content-Type value")
    async def _bulk_get(self, docs, **params):
        return await self._remote._post(
            f"{self.endpoint}/_bulk_get", {"docs": docs}, params
        )

    @raises(400, "The request provided invalid JSON data")
    @raises(417, "At least one document was rejected by the validation function")
    async def _bulk_docs(self, docs, **data):
        data["docs"] = docs
        return await self._remote._post(f"{self.endpoint}/_bulk_docs", data)

    @raises(400, "Invalid request")
    @raises(401, "Read privilege required for document '{id}'")
    @raises(500, "Query execution failed", RuntimeError)
    async def _find(self, selector, **data):
        data["selector"] = selector
        return await self._remote._post(f"{self.endpoint}/_find", data)


class RemoteDocument(object):
    def __init__(self, database, id):
        self._database = database
        self.id = id

    @property
    def endpoint(self):
        return f"{self._database.endpoint}/{_quote_id(self.id)}"

    @raises(401, "Read privilege required for document '{id}'")
    async def _exists(self):
        try:
            await self._database._remote._head(self.endpoint)
            return True
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                return False
            else:
                raise e

    @raises(400, "The format of the request or revision was invalid")
    @raises(401, "Read privilege required for document '{id}'")
    @raises(404, "Document {id} was not found")
    async def _get(self, **params):
        return await self._database._remote._get(self.endpoint, params)

    @raises(400, "The format of the request or revision was invalid")
    @raises(401, "Write privilege required for document '{id}'")
    @raises(404, "Specified database or document ID doesn’t exists ({endpoint})")
    @raises(
        409,
        "Document with the specified ID ({id}) already exists or specified revision {rev} is not latest for target document",
    )
    async def _put(self, data, **params):
        return await self._database._remote._put(self.endpoint, data, params)

    @raises(400, "Invalid request body or parameters")
    @raises(401, "Write privilege required for document '{id}'")
    @raises(404, "Specified database or document ID doesn’t exists ({endpoint})")
    @raises(
        409, "Specified revision ({rev}) is not the latest for target document '{id}'"
    )
    async def _delete(self, rev, **params):
        params["rev"] = rev
        return await self._database._remote._delete(self.endpoint, params)

    @raises(400, "Invalid request body or parameters")
    @raises(401, "Read or write privileges required")
    @raises(
        404, "Specified database, document ID or revision doesn’t exists ({endpoint})"
    )
    @raises(
        409,
        "Document with the specified ID already exists or specified revision is not latest for target document",
    )
    async def _copy(self, destination, **params):
        return await self._database._remote._request(
            "COPY", self.endpoint, params=params, headers={"Destination": destination}
        )


class RemoteView(object):
    def __init__(self, database, ddoc, id):
        self._database = database
        self.ddoc = ddoc
        self.id = id

    @property
    def endpoint(self):
        return f"{self._database.endpoint}/_design/{_quote_id(self.ddoc)}/_view/{_quote_id(self.id)}"

    @raises(400, "Invalid request")
    @raises(401, "Read privileges required")
    @raises(404, "Specified database, design document or view is missing")
    async def _get(self, **params):
        return await self._database._remote._get(self.endpoint, params)

    @raises(400, "Invalid request")
    @raises(401, "Read privileges required")
    @raises(404, "Specified database, design document or view is missing")
    async def _post(self, keys, **params):
        return await self._database._remote._post(self.endpoint, {"keys": keys}, params)
