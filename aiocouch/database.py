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

from .remote import RemoteDatabase
from .document import Document
from .view import AllDocsView


class Database(RemoteDatabase):
    def __init__(self, couchdb, id):
        super().__init__(couchdb._server, id)

    async def akeys(self, keys=None):
        data = await self._all_docs(keys)

        for row in data["rows"]:
            yield row["id"]

    async def create(self, id, exists_ok=False):
        doc = Document(self, id)

        if await doc._exists():
            if exists_ok:
                await doc.fetch(discard_changes=True)
            else:
                raise KeyError(
                    f"The document '{id}' does already exists in the database '{self.id}'"
                )

        return doc

    async def delete(self):
        await self._delete()

    async def docs(self, ids=None, create=False, **params):
        view = AllDocsView(self)
        if ids is None:
            iter = view.get(**params)
        else:
            iter = view.post(ids, create=create, **params)

        async for doc in iter:
            yield doc

    async def values(self, **params):
        view = AllDocsView(self)
        async for doc in view.get(**params):
            yield doc

    # TODO implement this for request with rev [{"id": id, "rev": rev},...]
    # async def bulk_docs(self, ids, create=False):
    #     request = []
    #
    #     for id in ids:
    #         request.append({"id": id})
    #
    #     docs = await self._bulk_get(request)
    #
    #     for data in docs["results"]:
    #         doc = Document(self, data["id"])
    #
    #         assert len(data["docs"]) == 1
    #
    #         if "ok" in data["docs"][0]:
    #             doc._update_cache(data["docs"][0]["ok"])
    #             yield doc
    #         elif create:
    #             yield doc
    #         else:
    #             raise KeyError(
    #                 f"The document '{doc.id}' could not be retrieved: {data['docs'][0]['error']['reason']}"
    #             )

    async def find(self, selector, limit=250, **params):
        if "fields" in selector.keys():
            del selector["fields"]

        while True:
            result_chunk = await self._find(selector, limit=limit, **params)

            for res in result_chunk["docs"]:
                doc = Document(self, res["_id"])
                doc._update_cache(res)
                yield doc

            if len(result_chunk["docs"]) < limit:
                break

            params["bookmark"] = result_chunk["bookmark"]

    def update_docs(self, ids, create=False):
        return BulkOperation(self, ids, create)

    async def __getitem__(self, id):
        doc = Document(self, id)
        await doc.fetch(discard_changes=True)
        return doc


class BulkOperation(object):
    def __init__(self, database, ids, create):
        self._database = database
        self._ids = ids
        self._create = create
        self.status = None

    async def __aenter__(self):
        self._docs = [
            doc async for doc in self._database.docs(self._ids, create=self._create)
        ]
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        # @VTTI: Yes, we actually need doc._data and not doc.data here
        docs = [doc._data for doc in self._docs if doc._dirty_cache]

        if docs:
            self.status = await self._database._bulk_docs(docs)

    async def __aiter__(self):
        for doc in self._docs:
            yield doc
