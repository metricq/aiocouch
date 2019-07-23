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

import aiohttp
import asyncio


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
    def __init__(self, server, user=None, password=None, **kwargs):
        self._server = server
        self._http_session = aiohttp.ClientSession(
            auth=aiohttp.BasicAuth(user, password), **kwargs
        )
        self._databases = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    @staticmethod
    async def _check_return_code(method, resp):
        # print("------- New Request -------")
        # print(f"{resp.request_info}:")
        # print(f"Received from {resp.method} {resp.url}: {resp}")

        if resp.status in range(200, 300):
            return

        if resp.status == 302:
            return

        url = resp.url

        if resp.status == 404:
            raise KeyError(
                f"The request ({method} {url}) returned an error '{resp.reason}' ({resp.status})"
            )
        elif resp.status in range(400, 500):
            json = await resp.json()
            if json and "reason" in json:
                reason = f": '{json['reason']}'"
            else:
                reason = ""
            raise RuntimeError(
                f"The request ({method} {url}) returned an error '{resp.reason}' ({resp.status}){reason}"
            )
        elif resp.status == 500:
            raise RuntimeError(
                f"The request ({method} {url}) returned an internal server error (500)"
            )

        raise NotImplementedError(
            f"The request ({method} {url}) returned an unexpected result ({resp.status}): '{resp.reason}'"
        )

    async def _get(self, path, params=None):
        return await self._request("GET", path, params=params)

    async def _put(self, path, data=None, params=None):
        return await self._request("PUT", path, json=data, params=params)

    async def _post(self, path, data, params=None):
        return await self._request("POST", path, json=data, params=params)

    async def _patch(self, path, data, params=None):
        return await self._request("PATCH", path, json=data, params=params)

    async def _delete(self, path, params=None):
        return await self._request("DELETE", path, params=params)

    async def _head(self, path, params=None):
        return await self._request("HEAD", path, params=params)

    async def _request(self, method, path, params, **kwargs):
        kwargs["params"] = _stringify_params(params)

        async with self._http_session.request(
            method, url=f"{self._server}{path}", **kwargs
        ) as resp:
            await self._check_return_code(method, resp)
            return await resp.json()

    async def _all_dbs(self, **params):
        return await self._get("/_all_dbs", params)

    async def close(self):
        await self._http_session.close()
        await asyncio.sleep(0.250)


class RemoteDatabase(object):
    def __init__(self, remote, id):
        self.id = id
        self._remote = remote

    @property
    def end_point(self):
        return f"/{self.id}"

    async def _exists(self):
        try:
            await self._remote._head(self.end_point)
            return True
        except KeyError:
            return False

    async def _get(self):
        return self._remote._get(self.end_point)

    async def _put(self, **params):
        return await self._remote._put(self.end_point)

    async def _delete(self):
        await self._remote._delete(self.end_point)

    async def _all_docs(self, keys=None, **params):
        return await self._remote._post(
            f"{self.end_point}/_all_docs", {"keys": keys} if keys is not None else {}, params
        )

    async def _bulk_get(self, docs, **params):
        return await self._remote._post(
            f"{self.end_point}/_bulk_get", {"docs": docs}, params
        )

    async def _bulk_docs(self, docs, **data):
        data["docs"] = docs
        return await self._remote._post(f"{self.end_point}/_bulk_docs", data)

    async def _find(self, selector, **data):
        data["selector"] = selector
        return await self._remote._post(f"{self.end_point}/_find", data)


class RemoteDocument(object):
    def __init__(self, database, id):
        self._database = database
        self.id = id

    @property
    def endpoint(self):
        return f"/{self._database.id}/{self.id}"

    async def _exists(self):
        try:
            await self._database._remote._head(self.endpoint)
            return True
        except KeyError:
            return False

    async def _get(self, **params):
        return await self._database._remote._get(self.endpoint, params)

    async def _put(self, data, **params):
        return await self._database._remote._put(self.endpoint, data, params)

    async def _delete(self, rev, **params):
        params["rev"] = rev
        return await self._database._remote._delete(self.endpoint, params)

    async def _copy(self, destination, **params):
        return await self._database._remote._request(
            "COPY", self.endpoint, params=params, headers={"Destination": destination}
        )

    async def _create(self, data, **params):
        await self._database._remote._post(f"/{self._database.id}", data, params)


class RemoteView(object):
    def __init__(self, database, ddoc, id):
        self._database = database
        self.ddoc = ddoc
        self.id = id

    @property
    def endpoint(self):
        return f"/{self._database.id}/_design/{self.ddoc}/_view/{self.id}"

    async def _get(self, **params):
        return await self._database._remote._get(self.endpoint, params)

    async def _post(self, keys, **params):
        return await self._database._remote._post(self.endpoint, {"keys": keys}, params)


class RemoteAllDocsView(RemoteView):
    def __init__(self, database):
        super().__init__(database, None, "_all_docs")

    @property
    def endpoint(self):
        return f"/{self._database.id}/_all_docs"
