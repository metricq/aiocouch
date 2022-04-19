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

from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional, Tuple

from . import database
from .document import Document
from .exception import NotFoundError
from .remote import RemoteView

JsonDict = Dict[str, Any]


@dataclass(frozen=True)
class ViewResponse:
    _database: "database.Database"
    offset: int
    rows: List[JsonDict]
    total_rows: int
    update_seq: Any = None

    def keys(self) -> Generator[str, None, None]:
        for row in self.rows:
            if "error" not in row:
                yield row["id"]

    def values(self) -> Generator[Tuple[str, Any], None, None]:
        for row in self.rows:
            if "error" not in row:
                yield row["value"]

    def items(self) -> Generator[Any, None, None]:
        for row in self.rows:
            if "error" not in row:
                yield row["key"], row["value"],

    def docs(
        self,
        create: bool = False,
        include_ddocs: bool = False,
    ) -> Generator[Document, None, None]:
        for row in self.rows:
            if "error" not in row and row["doc"] is not None:
                if row["id"].startswith("_design/") and not include_ddocs:
                    continue
                doc = Document(self._database, row["id"])
                doc._update_cache(row["doc"])
                yield doc
            elif create:
                doc = Document(self._database, row["key"])
                yield doc
            else:
                raise NotFoundError(
                    f"The document '{row['key']}' does not exist in the database "
                    f"{self._database.id}."
                )


class View(RemoteView):
    def __init__(
        self, database: "database.Database", design_doc: Optional[str], id: str
    ):
        super().__init__(database, design_doc, id)

    @property
    def prefix_sentinal(self) -> str:
        return "\uffff"

    async def get(self, **params: Any) -> ViewResponse:
        return ViewResponse(_database=self._database, **(await self._get(**params)))

    async def post(self, ids: List[str], **params: Any) -> ViewResponse:
        return ViewResponse(
            _database=self._database, **(await self._post(ids, **params))
        )

    async def akeys(self, **params: Any) -> AsyncGenerator[str, None]:
        for key in (await self.get(**params)).keys():
            yield key

    async def aitems(self, **params: Any) -> AsyncGenerator[Tuple[str, Any], None]:
        for key, value in (await self.get(**params)).items():
            yield key, value,

    async def avalues(self, **params: Any) -> AsyncGenerator[Any, None]:
        for value in (await self.get(**params)).values():
            yield value

    async def ids(
        self,
        keys: Optional[List[str]] = None,
        prefix: Optional[str] = None,
        **params: Any,
    ) -> AsyncGenerator[str, None]:
        if prefix is not None:
            params["startkey"] = f'"{prefix}"'
            params["endkey"] = f'"{prefix}{self.prefix_sentinal}"'

        response = await (
            self.get(**params) if keys is None else self.post(keys, **params)
        )

        for key in response.keys():
            yield key

    async def docs(
        self,
        ids: Optional[List[str]] = None,
        create: bool = False,
        prefix: Optional[str] = None,
        include_ddocs: bool = False,
        **params: Any,
    ) -> AsyncGenerator[Document, None]:
        params["include_docs"] = True
        if prefix is not None:
            if ids is not None or create:
                raise ValueError(
                    "prefix cannot be used together with ids or create parameter"
                )

            params["startkey"] = f'"{prefix}"'
            params["endkey"] = f'"{prefix}{self.prefix_sentinal}"'

        response = await (
            self.get(**params) if ids is None else self.post(ids, **params)
        )

        for doc in response.docs(create=create, include_ddocs=include_ddocs):
            yield doc


class AllDocsView(View):
    def __init__(self, database: "database.Database"):
        super().__init__(database, None, "_all_docs")

    @property
    def endpoint(self) -> str:
        return f"/{self._database.id}/_all_docs"

    @property
    def prefix_sentinal(self) -> str:
        return chr(0x10FFFE)
