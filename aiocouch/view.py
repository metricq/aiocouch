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

from .document import Document
from .exception import NotFoundError
from .remote import RemoteView


class View(RemoteView):
    def __init__(self, database, design_doc, id):
        super().__init__(database, design_doc, id)

    @property
    def prefix_sentinal(self):
        return "\uffff"

    async def get(self, **params):
        result_chunk = await self._get(**params)

        for res in result_chunk["rows"]:
            yield res

    async def post(self, ids, create=False, **params):
        result_chunk = await self._post(ids, **params)

        for res in result_chunk["rows"]:
            yield res

    async def ids(self, keys=None, prefix=None, **params):
        if prefix is not None:
            params["startkey"] = f'"{prefix}"'
            params["endkey"] = f'"{prefix}{self.prefix_sentinal}"'

        if keys is None:
            async for res in self.get(**params):
                if "error" not in res:
                    yield res["id"]
        else:
            async for res in self.post(keys, **params):
                if "error" not in res:
                    yield res["id"]

    async def akeys(self, **params):
        async for res in self.get(**params):
            yield res["key"]

    async def aitems(self, **params):
        async for res in self.get(**params):
            yield res["key"], res["value"]

    async def avalues(self, **params):
        async for res in self.get(**params):
            yield res["value"]

    async def docs(self, ids=None, create=False, prefix=None, **params):
        params["include_docs"] = True
        if prefix is None:
            if ids is None:
                iter = self.get(**params)
            else:
                iter = self.post(ids, **params)
        else:
            if ids is not None or create:
                raise ValueError(
                    "prefix cannot be used together with ids or create parameter"
                )

            params["startkey"] = f'"{prefix}"'
            params["endkey"] = f'"{prefix}{self.prefix_sentinal}"'

            iter = self.get(**params)

        async for res in iter:
            if "error" not in res and res["doc"] is not None:
                doc = Document(self._database, res["id"])
                doc._update_cache(res["doc"])
                yield doc
            elif create:
                doc = Document(self._database, res["key"])
                yield doc
            else:
                raise NotFoundError(
                    f"The document '{res['key']}' does not exist in the database "
                    f"{self._database.id}."
                )


class AllDocsView(View):
    def __init__(self, database):
        super().__init__(database, None, "_all_docs")

    @property
    def endpoint(self):
        return f"/{self._database.id}/_all_docs"

    @property
    def prefix_sentinal(self):
        return chr(0x10FFFE)
