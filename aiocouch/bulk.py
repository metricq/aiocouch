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


class BulkStoreOperation(object):
    def __init__(self, database, ids=[]):
        self._database = database
        self._ids = ids
        self.status = None
        self.ok = None
        self.error = None

    async def __aenter__(self):
        self._docs = [Document(self._database, id) for id in self._ids]
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        # @VTTI: Yes, we actually need doc._data and not doc.data here
        docs = [doc._data for doc in self._docs if doc._dirty_cache]

        if docs:
            self.status = await self._database._bulk_docs(docs)
        else:
            self.status = []

        self.ok = []
        self.error = []

        docs = [doc for doc in self._docs if doc._dirty_cache]
        for status, doc in zip(self.status, docs):
            assert status["id"] == doc.id
            if "ok" in status:
                doc._update_rev_after_save(status)
                self.ok.append(doc)
            else:
                self.error.append(doc)

    async def __aiter__(self):
        for doc in self._docs:
            yield doc

    def create(self, id, data=None):
        doc = Document(self._database, id, data=data)
        self._docs.append(doc)

        return doc


class BulkOperation(BulkStoreOperation):
    def __init__(self, database, ids, create):
        super().__init__(database, ids=ids)
        self._create = create

    async def __aenter__(self):
        self._docs = [
            doc async for doc in self._database.docs(self._ids, create=self._create)
        ]
        return self
