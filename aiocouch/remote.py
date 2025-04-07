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

import asyncio
import json
from contextlib import suppress
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple, Union, cast
from urllib.parse import quote

import aiohttp

from . import database, document
from .exception import NotFoundError, RemoteResponseError, generator_raises, raises
from .typing import JsonDict


class HTTPResponse:
    """Represents an HTTP response from the CouchDB server."""

    status: int
    """The HTTP response status, usually 200, 201 or 202"""

    headers: Dict[str, str]
    """The HTTP headers of the response"""

    def __init__(self, resp: aiohttp.client.ClientResponse):
        self.status = resp.status
        self.headers = dict(resp.headers)

    @property
    def etag(self) -> Optional[str]:
        """Convenient property to access the ETag header in a usable format"""
        return self.headers["Etag"][1:-1] if "Etag" in self.headers else None


RequestResult = Tuple[HTTPResponse, Union[bytes, JsonDict]]


def _quote_id(id: str) -> str:
    return quote(id, safe="")


def _stringify_params(params: Optional[JsonDict]) -> Optional[JsonDict]:
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


class RemoteServer:
    def __init__(
        self,
        server: str,
        *,
        user: Optional[str] = None,
        password: Optional[str] = None,
        cookie: Optional[str] = None,
        **kwargs: Any,
    ):
        self._server = server
        auth = aiohttp.BasicAuth(user, password, "utf-8") if user and password else None
        headers = {"Cookie": "AuthSession=" + cookie} if cookie else None
        self._http_session = aiohttp.ClientSession(headers=headers, auth=auth, **kwargs)

    async def _get(
        self, path: str, *, params: Optional[JsonDict] = None
    ) -> RequestResult:
        return await self._request("GET", path, params=params)

    async def _get_bytes(
        self, path: str, *, params: Optional[JsonDict] = None
    ) -> RequestResult:
        return await self._request("GET", path, params=params, return_json=False)

    async def _put(
        self,
        path: str,
        *,
        data: Optional[JsonDict] = None,
        params: Optional[JsonDict] = None,
    ) -> RequestResult:
        return await self._request("PUT", path, json=data, params=params)

    async def _put_bytes(
        self,
        path: str,
        *,
        data: bytes,
        content_type: str,
        params: Optional[JsonDict] = None,
    ) -> RequestResult:
        return await self._request(
            "PUT",
            path,
            data=data,
            params=params,
            headers={"Content-Type": content_type},
        )

    async def _post(
        self, path: str, *, data: JsonDict, params: Optional[JsonDict] = None
    ) -> RequestResult:
        return await self._request("POST", path, json=data, params=params)

    async def _delete(
        self, path: str, *, params: Optional[JsonDict] = None
    ) -> RequestResult:
        return await self._request("DELETE", path, params=params)

    async def _head(
        self,
        path: str,
        *,
        params: Optional[JsonDict] = None,
        **kwargs: Any,
    ) -> RequestResult:
        return await self._request("HEAD", path, params=params, **kwargs)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[JsonDict] = None,
        return_json: bool = True,
        **kwargs: Any,
    ) -> RequestResult:
        kwargs["params"] = _stringify_params(params) if params else {}

        async with self._http_session.request(
            method, url=f"{self._server}{path}", **kwargs
        ) as resp:
            reason = None
            with suppress(Exception):
                reason = (await resp.json())["reason"]
            try:
                resp.raise_for_status()
            except aiohttp.ClientResponseError:
                raise RemoteResponseError(
                    reason,
                    resp.request_info,
                    resp.history,
                    status=resp.status,
                    message=resp.reason,
                    headers=resp.headers,
                )

            return (
                HTTPResponse(resp),
                await resp.json() if return_json else await resp.read(),
            )

    async def _streamed_request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[JsonDict] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[JsonDict, None]:
        kwargs["params"] = _stringify_params(params) if params else {}
        kwargs.setdefault("timeout", aiohttp.ClientTimeout())

        async with self._http_session.request(
            method, url=f"{self._server}{path}", **kwargs
        ) as resp:
            try:
                resp.raise_for_status()
            except aiohttp.ClientResponseError:
                raise RemoteResponseError(
                    None,
                    resp.request_info,
                    resp.history,
                    status=resp.status,
                    message=resp.reason,
                    headers=resp.headers,
                )

            async for line in resp.content:
                # this should only happen for empty lines
                with suppress(json.JSONDecodeError):
                    yield json.loads(line)

    @raises(401, "Invalid credentials")
    @raises(403, "Access forbidden: {reason}")
    async def _all_dbs(self, **params: Any) -> List[str]:
        _, json = await self._get("/_all_dbs", params=params)
        assert not isinstance(json, bytes)
        return cast(List[str], json)

    async def close(self) -> None:
        # If ClientSession has TLS/SSL connections, it is needed to wait 250 ms
        # before closing, see https://github.com/aio-libs/aiohttp/issues/1925.
        has_ssl_conn = self._http_session.connector and any(
            any(hasattr(handler.transport, "_ssl_protocol") for handler, _ in conn)
            for conn in self._http_session.connector._conns.values()
        )
        await self._http_session.close()
        await asyncio.sleep(0.250 if has_ssl_conn else 0)

    @raises(401, "Invalid credentials")
    @raises(403, "Access forbidden: {reason}")
    async def _info(self) -> JsonDict:
        _, json = await self._get("/")
        assert not isinstance(json, bytes)
        return json

    @raises(401, "Authentication failed, check provided credentials.")
    @raises(403, "Access forbidden: {reason}")
    async def _check_session(self) -> RequestResult:
        return await self._get("/_session")


class RemoteDatabase:
    def __init__(self, remote: RemoteServer, id: str):
        self.id = id
        self._remote = remote

    @property
    def endpoint(self) -> str:
        return f"/{_quote_id(self.id)}"

    @raises(401, "Invalid credentials")
    @raises(403, "Access forbidden: {reason}")
    async def _exists(self) -> bool:
        try:
            await self._remote._head(self.endpoint)
            return True
        except RemoteResponseError as e:
            if e.status == 404:
                return False
            else:
                raise e

    @raises(401, "Invalid credentials")
    @raises(403, "Access forbidden: {reason}")
    @raises(404, "Requested database not found ({id})")
    async def _get(self) -> JsonDict:
        _, json = await self._remote._get(self.endpoint)
        assert not isinstance(json, bytes)
        return json

    @raises(400, "Invalid database name")
    @raises(401, "CouchDB Server Administrator privileges required")
    @raises(403, "Access forbidden: {reason}")
    @raises(412, "Database already exists")
    async def _put(self, **params: Any) -> JsonDict:
        _, json = await self._remote._put(self.endpoint, params=params)
        assert not isinstance(json, bytes)
        return json

    @raises(400, "Invalid database name or forgotten document id by accident")
    @raises(401, "CouchDB Server Administrator privileges required")
    @raises(403, "Access forbidden: {reason}")
    @raises(404, "Database doesn't exist or invalid database name ({id})")
    async def _delete(self) -> None:
        await self._remote._delete(self.endpoint)

    @raises(400, "The request provided invalid JSON data or invalid query parameter")
    @raises(401, "Read permission required")
    @raises(403, "Access forbidden: {reason}")
    @raises(404, "Invalid database name")
    @raises(415, "Bad Content-Type value")
    async def _bulk_get(self, docs: List[str], **params: Any) -> JsonDict:
        _, json = await self._remote._post(
            f"{self.endpoint}/_bulk_get",
            data={"docs": docs},
            params=params,
        )
        assert not isinstance(json, bytes)
        return json

    @raises(400, "The request provided invalid JSON data")
    @raises(401, "Invalid credentials")
    @raises(403, "Access forbidden: {reason}")
    @raises(417, "At least one document was rejected by the validation function")
    async def _bulk_docs(self, docs: List[JsonDict], **data: Any) -> JsonDict:
        data["docs"] = docs
        _, json = await self._remote._post(
            f"{self.endpoint}/_bulk_docs",
            data=data,
        )
        assert not isinstance(json, bytes)
        return json

    @raises(400, "Invalid request")
    @raises(401, "Read privilege required for document '{id}'")
    @raises(403, "Access forbidden: {reason}")
    @raises(500, "Query execution failed", RuntimeError)
    async def _find(self, selector: Any, **data: Any) -> JsonDict:
        data["selector"] = selector
        _, json = await self._remote._post(
            f"{self.endpoint}/_find",
            data=data,
        )
        assert not isinstance(json, bytes)
        return json

    @raises(400, "Invalid request")
    @raises(401, "Admin permission required")
    @raises(403, "Access forbidden: {reason}")
    @raises(404, "Database not found")
    @raises(500, "Execution error")
    async def _index(self, index: JsonDict, **data: Any) -> JsonDict:
        data["index"] = index
        _, json = await self._remote._post(
            f"{self.endpoint}/_index",
            data=data,
        )
        assert not isinstance(json, bytes)
        return json

    @raises(401, "Invalid credentials")
    @raises(403, "Access forbidden: {reason}")
    async def _get_security(self) -> JsonDict:
        _, json = await self._remote._get(f"{self.endpoint}/_security")
        assert not isinstance(json, bytes)
        return json

    @raises(401, "Invalid credentials")
    @raises(403, "Access forbidden: {reason}")
    async def _put_security(self, doc: JsonDict) -> JsonDict:
        _, json = await self._remote._put(
            f"{self.endpoint}/_security",
            data=doc,
        )
        assert not isinstance(json, bytes)
        return json

    @generator_raises(400, "Invalid request")
    @generator_raises(403, "Access forbidden: {reason}")
    async def _changes(self, **params: Any) -> AsyncGenerator[JsonDict, None]:
        if "feed" in params and params["feed"] == "continuous":
            params.setdefault("heartbeat", True)
            async for data in self._remote._streamed_request(
                "GET", f"{self.endpoint}/_changes", params=params
            ):
                yield data
        else:
            _, json = await self._remote._get(
                f"{self.endpoint}/_changes", params=params
            )
            assert not isinstance(json, bytes)
            for result in json["results"]:
                yield result

    @raises(400, "Invalid database or JSON payload")
    @raises(403, "Access forbidden: {reason}")
    @raises(415, "Bad Content-Type header value")
    @raises(500, "Internal server error or timeout")
    async def _purge(self, docs: JsonDict, **params: Any) -> JsonDict:
        _, json = await self._remote._post(
            f"{self.endpoint}/_purge", data=docs, params=params
        )
        assert not isinstance(json, bytes)
        return json


class RemoteDocument:
    def __init__(self, database: "database.Database", id: str):
        self._database = database
        self.id = id
        self._data: Optional[JsonDict] = None

    @property
    def endpoint(self) -> str:
        return f"{self._database.endpoint}/{_quote_id(self.id)}"

    @raises(401, "Read privilege required for document '{id}'")
    @raises(403, "Access forbidden: {reason}")
    @raises(404, "Document {id} was not found")
    async def _head(self) -> None:
        await self._database._remote._head(self.endpoint)

    @raises(401, "Read privilege required for document '{id}'")
    @raises(403, "Access forbidden: {reason}")
    @raises(404, "Document {id} was not found")
    async def _info(self) -> JsonDict:
        response, _ = await self._database._remote._head(self.endpoint)
        assert self._data is not None
        return {
            "ok": True,
            "id": self._data["_id"],
            "rev": response.headers["Etag"][1:-1],
        }

    async def _exists(self) -> bool:
        try:
            await self._head()
            return True
        except NotFoundError:
            return False

    @raises(400, "The format of the request or revision was invalid")
    @raises(401, "Read privilege required for document '{id}'")
    @raises(403, "Access forbidden: {reason}")
    @raises(404, "Document {id} was not found")
    async def _get(self, **params: Any) -> JsonDict:
        _, json = await self._database._remote._get(
            self.endpoint,
            params=params,
        )
        assert not isinstance(json, bytes)
        return json

    @raises(400, "The format of the request or revision was invalid")
    @raises(401, "Write privilege required for document '{id}'")
    @raises(403, "Access forbidden: {reason}")
    @raises(404, "Specified database or document ID doesn't exists ({endpoint})")
    @raises(
        409,
        "Document with the specified ID ({id}) already exists or specified revision "
        "{rev} is not latest for target document",
    )
    async def _put(
        self, data: JsonDict, **params: Any
    ) -> Tuple[HTTPResponse, JsonDict]:
        response, json = await self._database._remote._put(
            self.endpoint,
            data=data,
            params=params,
        )
        assert not isinstance(json, bytes)
        return (response, json)

    @raises(400, "Invalid request body or parameters")
    @raises(401, "Write privilege required for document '{id}'")
    @raises(403, "Access forbidden: {reason}")
    @raises(404, "Specified database or document ID doesn't exists ({endpoint})")
    @raises(
        409, "Specified revision ({rev}) is not the latest for target document '{id}'"
    )
    async def _delete(self, rev: str, **params: Any) -> Tuple[HTTPResponse, JsonDict]:
        params["rev"] = rev
        response, json = await self._database._remote._delete(
            self.endpoint,
            params=params,
        )
        assert not isinstance(json, bytes)
        return (response, json)

    @raises(400, "Invalid request body or parameters")
    @raises(401, "Read or write privileges required")
    @raises(403, "Access forbidden: {reason}")
    @raises(
        404, "Specified database, document ID or revision doesn't exists ({endpoint})"
    )
    @raises(
        409,
        "Document with the specified ID already exists or specified revision is not "
        "latest for target document",
    )
    async def _copy(
        self, destination: str, **params: Any
    ) -> Tuple[HTTPResponse, JsonDict]:
        response, json = await self._database._remote._request(
            "COPY",
            self.endpoint,
            params=params,
            headers={"Destination": destination},
        )
        assert not isinstance(json, bytes)
        return (response, json)

    @raises(400, "The format of the request or revision was invalid")
    @raises(401, "Read privilege required for document '{id}'")
    @raises(403, "Access forbidden: {reason}")
    @raises(404, "Document {id} was not found")
    async def _conflicts(self) -> List[str]:
        json = await self._get(conflicts=True)
        assert not isinstance(json, bytes)
        return cast(List[str], json.get("_conflicts", []))

    @raises(400, "The format of the request or revision was invalid")
    @raises(401, "Read privilege required for document '{id}'")
    @raises(403, "Access forbidden: {reason}")
    @raises(404, "Document {id} was not found")
    async def _revs(self) -> List[str]:
        json = await self._get(revs_info=True)
        assert not isinstance(json, bytes)
        return cast(List[str], [item["rev"] for item in json.get("_revs_info", [])])


class RemoteAttachment:
    def __init__(self, document: "document.Document", id: str):
        self._document = document
        self.id = id
        self.content_type: Optional[str] = None

    @property
    def endpoint(self) -> str:
        return f"{self._document.endpoint}/{_quote_id(self.id)}"

    @raises(401, "Read privilege required for document '{document_id}'")
    @raises(403, "Access forbidden: {reason}")
    async def _exists(self) -> bool:
        try:
            response, _ = await self._document._database._remote._head(
                self.endpoint, return_json=False
            )
            self.content_type = response.headers["Content-Type"]
            return True
        except RemoteResponseError as e:
            if e.status == 404:
                return False
            else:
                raise e

    @raises(400, "Invalid request parameters")
    @raises(401, "Read privilege required for document '{document_id}'")
    @raises(403, "Access forbidden: {reason}")
    @raises(404, "Document '{document_id}' or attachment '{id}' doesn't exists")
    async def _get(self, **params: Any) -> bytes:
        response, data = await self._document._database._remote._get_bytes(
            self.endpoint,
            params=params,
        )
        self.content_type = response.headers["Content-Type"]
        assert isinstance(data, bytes)
        return data

    @raises(400, "Invalid request body or parameters")
    @raises(401, "Write privilege required for document '{document_id}'")
    @raises(403, "Access forbidden: {reason}")
    @raises(404, "Document '{document_id}' doesn't exists")
    @raises(
        409, "Specified revision {document_rev} is not the latest for target document"
    )
    async def _put(
        self, rev: str, data: bytes, content_type: str, **params: Any
    ) -> JsonDict:
        params["rev"] = rev
        _, json = await self._document._database._remote._put_bytes(
            self.endpoint,
            data=data,
            content_type=content_type,
            params=params,
        )
        self.content_type = content_type
        assert not isinstance(json, bytes)
        return json

    @raises(400, "Invalid request body or parameters")
    @raises(401, "Write privilege required for document '{document_id}'")
    @raises(403, "Access forbidden: {reason}")
    @raises(404, "Specified database or document ID doesn't exists ({endpoint})")
    @raises(
        409, "Specified revision {document_rev} is not the latest for target document"
    )
    async def _delete(self, rev: str, **params: Any) -> JsonDict:
        params["rev"] = rev
        _, json = await self._document._database._remote._delete(
            self.endpoint,
            params=params,
        )
        self.content_type = None
        assert not isinstance(json, bytes)
        return json


class RemoteView:
    def __init__(self, database: "database.Database", ddoc: Optional[str], id: str):
        self._database = database
        self.ddoc = ddoc
        self.id = id

    @property
    def endpoint(self) -> str:
        assert self.ddoc is not None
        return (
            f"{self._database.endpoint}/_design/{_quote_id(self.ddoc)}/_view/"
            f"{_quote_id(self.id)}"
        )

    @raises(400, "Invalid request")
    @raises(401, "Read privileges required")
    @raises(403, "Access forbidden: {reason}")
    @raises(404, "Specified database, design document or view is missing")
    async def _get(self, **params: Any) -> JsonDict:
        _, json = await self._database._remote._get(
            self.endpoint,
            params=params,
        )
        assert not isinstance(json, bytes)
        return json

    @raises(400, "Invalid request")
    @raises(401, "Write privileges required")
    @raises(403, "Access forbidden: {reason}")
    @raises(404, "Specified database, design document or view is missing")
    async def _post(self, keys: List[str], **params: Any) -> JsonDict:
        _, json = await self._database._remote._post(
            self.endpoint,
            data={"keys": keys},
            params=params,
        )
        assert not isinstance(json, bytes)
        return json
