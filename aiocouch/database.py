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


class Database(RemoteDatabase):
    def __init__(self, couchdb, name):
        super().__init__(couchdb._server, name)
        self._couchdb = couchdb
        self._document_cache = {}

    async def akeys(self, keys=None):
        data = await self._all_docs(keys)

        for row in data["rows"]:
            yield row["id"]

    async def get(self, name):
        doc = self[name]

        if await doc._exists():
            await doc.fetch(discard_changes=True)

        return doc

    async def delete(self):
        await self._delete()

    async def get_all(self, names):
        request = []

        if isinstance(names, str):
            names = [names]

        for name in names:
            self[name]
            request.append({"id": name})

        docs = await self._bulk_get(request)

        for data in docs["results"]:
            doc = self[data["id"]]

            if "ok" in data["docs"][0]:
                doc._update_cache(data["docs"][0]["ok"])

            yield doc

    async def find(self, selector, limit=250, **params):
        if "fields" in selector.keys():
            del selector["fields"]

        while True:
            result_chunk = await self._find(selector, limit=limit, **params)

            for res in result_chunk["docs"]:
                id = res["_id"]
                doc = self[id]
                doc._update_cache(res)
                yield doc

            if len(result_chunk["docs"]) < limit:
                break

            params["bookmark"] = result_chunk["bookmark"]

    async def save_all(self, docs=None):
        if docs is None:
            docs = [
                doc._cached_data
                for doc in self._document_cache.values()
                if doc._dirty_cache
            ]
        else:
            docs = [doc._cached_data for doc in docs]

        for res in await self._bulk_docs(docs):
            if "error" in res:
                # TODO propagate the error(s) to the user D:
                continue
            doc = self[res["id"]]
            doc._update_rev_after_save(res["rev"])

    def __getitem__(self, id):
        if id not in self._document_cache:
            self._document_cache[id] = Document(self, id)

        return self._document_cache[id]
