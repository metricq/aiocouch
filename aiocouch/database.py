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

from .bulk import BulkOperation, BulkStoreOperation
from .document import Document, SecurityDocument
from .design_document import DesignDocument
from .exception import ConflictError, NotFoundError
from .remote import RemoteDatabase
from .view import AllDocsView, View

from contextlib import suppress


class Database(RemoteDatabase):
    def __init__(self, couchdb, id):
        super().__init__(couchdb._server, id)

    async def akeys(self, **params):
        async for key in self.all_docs.ids(**params):
            yield key

    async def create(self, id, data=None, exists_ok=False):
        doc = Document(self, id, data=data)

        if exists_ok:
            with suppress(NotFoundError):
                await doc.fetch(discard_changes=True)
        else:
            if await doc._exists():
                raise ConflictError(
                    f"The document '{id}' does already exist in the database '{self.id}'"
                )

        return doc

    async def delete(self):
        await self._delete()

    async def docs(self, ids=None, create=False, prefix=None, **params):
        async for doc in self.all_docs.docs(ids, create, prefix, **params):
            yield doc

    async def values(self, **params):
        async for doc in self.all_docs.docs(**params):
            yield doc

    @property
    def all_docs(self):
        return AllDocsView(self)

    def view(self, design_doc, view):
        return View(self, design_doc, view)

    async def design_doc(self, id, exists_ok=False):
        ddoc = DesignDocument(self, id)

        if await ddoc._exists():
            if exists_ok:
                await ddoc.fetch(discard_changes=True)
            else:
                raise ConflictError(
                    f"The design document '{id}' does already exist in the database '{self.id}'"
                )

        return ddoc

    async def find(self, selector, limit=None, **params):
        # we need to get the complete doc, so fields selector isn't allowed
        if "fields" in selector.keys():
            raise ValueError("selector must not contain a fields entry")

        # We must use pagination because otherwise the default limit of the _find endpoint
        # fucks us
        pagination_size = limit if limit is not None else 10000

        while True:
            result_chunk = await self._find(selector, limit=pagination_size, **params)

            for res in result_chunk["docs"]:
                doc = Document(self, res["_id"])
                doc._update_cache(res)
                yield doc

            if len(result_chunk["docs"]) < pagination_size or limit is not None:
                break

            params["bookmark"] = result_chunk["bookmark"]

    def update_docs(self, ids, create=False):
        return BulkOperation(self, ids, create)

    def create_docs(self, ids=[]):
        return BulkStoreOperation(self, ids)

    async def __getitem__(self, id):
        return await self.get(id)

    async def get(self, id, default=None):
        doc = Document(self, id, data=default)

        try:
            await doc.fetch(discard_changes=True)
        except NotFoundError as e:
            if default is None:
                raise e

        return doc

    async def security(self):
        doc = SecurityDocument(self)
        await doc.fetch(discard_changes=True)
        return doc

    async def info(self):
        return await self._get()
