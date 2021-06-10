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

from types import TracebackType
from typing import Any, AsyncGenerator, Dict, List, Optional, Type, cast

from . import database
from .document import Document

JsonDict = Dict[str, Any]


class BulkStoreOperation:
    def __init__(self, database: "database.Database", ids: List[str] = []):
        self._database = database
        self._ids = ids
        self.status: Optional[List[JsonDict]] = None
        self.ok: Optional[List[Document]] = None
        self.error: Optional[List[Document]] = None
        self._docs: Optional[List[Document]] = None

    async def __aenter__(self) -> "BulkStoreOperation":
        self._docs = [Document(self._database, id) for id in self._ids]
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        assert self._docs is not None
        # @VTTI: Yes, we actually need doc._data and not doc.data here
        docs = [doc._data for doc in self._docs if doc._dirty_cache]

        if docs:
            self.status = cast(List[JsonDict], await self._database._bulk_docs(docs))
        else:
            self.status = []

        self.ok = []
        self.error = []

        result_docs = [doc for doc in self._docs if doc._dirty_cache]
        for status, doc in zip(self.status, result_docs):
            assert status["id"] == doc.id
            if "ok" in status:
                doc._update_rev_after_save(status)
                self.ok.append(doc)
            else:
                self.error.append(doc)

    async def __aiter__(self) -> AsyncGenerator[Document, None]:
        assert self._docs is not None
        for doc in self._docs:
            yield doc

    def create(self, id: str, data: Optional[JsonDict] = None) -> Document:
        """Creates a Document instance with the given data that will be stored as part of the BulkStoreOperation.

        Args:
            id (str): the
            data (Dict, optional): The data of the created Document. Defaults to None.

        Raises:
            ValueError: If the same document id is already part of the BulkStoreOperation

        Returns:
            The Document instance representing the document, which can be used to set the contents.
        """
        assert self._docs is not None
        if any(id == d.id for d in self._docs):
            raise ValueError(
                f"There is already another Document instance for {id} part of the BulkOperation"
            )

        doc = Document(self._database, id, data=data)
        self._docs.append(doc)

        return doc

    def update(self, doc: Document) -> Document:
        """Update the passed document as part of the BulkStoreOperation.

        Args:
            doc (Document): The used Document instance

        Raises:
            ValueError: If the same document id is already part of the BulkStoreOperation

        Returns:
            the passed Document instance
        """
        assert self._docs is not None
        if any(doc.id == d.id for d in self._docs):
            raise ValueError(
                f"There is already another Document instance for {doc.id} part of the BulkOperation"
            )

        self._docs.append(doc)
        return doc


class BulkOperation(BulkStoreOperation):
    def __init__(self, database: "database.Database", ids: List[str], create: bool):
        super().__init__(database=database, ids=ids)
        self._create = create

    async def __aenter__(self) -> "BulkOperation":
        self._docs = [
            doc async for doc in self._database.docs(self._ids, create=self._create)
        ]
        return self
