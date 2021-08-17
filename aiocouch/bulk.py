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

from deprecated.sphinx import deprecated

from . import database
from .document import Document

JsonDict = Dict[str, Any]


class BulkOperation:
    """A context manager for bulk operation. This operation allows to
    write many documents in one request.

    Bulk operations use the :ref:`_bulk_docs<couchdb:api/db/bulk_docs>`
    endpoint of the database.

    To populate the list of written documents, use the :meth:`append`
    method.

    :param database: The database used in the bulk operation
    """

    def __init__(self, database: "database.Database"):
        self._database = database

        self.response: Optional[List[JsonDict]] = None
        """The resulting JSON response of the :ref:`_bulk_docs<couchdb:api/db/bulk_docs>`
        request. Refer to the CouchDB documentation for the contents.

        Only available after the context manager has finished without a
        passing exception."""

        self.ok: Optional[List[Document]] = None
        """The list of all :class:`~aiocouch.document.Document` instances that there
        successfully saved to server.

        Only available after the context manager has finished without a
        passing exception."""

        self.error: Optional[List[Document]] = None
        """The list of all :class:`~aiocouch.document.Document` instances that could not
        be saved to server.

        Only available after the context manager has finished without a
        passing exception."""

        self._docs: List[Document] = []

    async def __aenter__(self) -> "BulkOperation":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        if exc_type is not None:
            return

        # @VTTI: Yes, we actually need doc._data and not doc.data here
        docs = [doc._data for doc in self._docs if doc._dirty_cache]

        if docs:
            self.response = cast(List[JsonDict], await self._database._bulk_docs(docs))
        else:
            self.response = []

        self.ok = []
        self.error = []

        result_docs = [doc for doc in self._docs if doc._dirty_cache]
        for status, doc in zip(self.response, result_docs):
            assert status["id"] == doc.id
            if "ok" in status:
                doc._update_rev_after_save(status)
                self.ok.append(doc)
            else:
                self.error.append(doc)

    async def __aiter__(self) -> AsyncGenerator[Document, None]:
        """An iterator that yields Document instances that are part of this bulk operation.

        :return: Every :class:`~aiocouch.document.Document` instance that will be affected by this operation
        :rtype: AsyncGenerator[Document, None]
        """
        for doc in self._docs:
            yield doc

    def create(self, id: str, data: Optional[JsonDict] = None) -> Document:
        """Create a new document as part of the bulk operation

        :param id: the id of the document
        :param data: the inital data used to set the body of the document, defaults to None
        :raises ValueError: if the provided document id is already part of the bulk operation
        :return: a Document instance reference the newly created document
        """
        if any(id == d.id for d in self._docs):
            raise ValueError(
                f"There is already another Document instance for {id} part of the BulkOperation"
            )

        doc = Document(self._database, id, data=data)
        self._docs.append(doc)

        return doc

    # Mypy isn't smart enough, see: https://github.com/python/mypy/issues/1362
    @property  # type:ignore
    @deprecated(version="2.1.0", reason="Use the response property instead.")
    def status(self) -> Optional[List[JsonDict]]:  # pragma: no cover
        return self.response

    @deprecated(
        version="2.1.0", reason="Use append(doc) instead. It just makes more sense."
    )
    def update(self, doc: Document) -> Document:  # pragma: no cover
        """Add a document to this bulk operation.

        :param doc: the document that should be stored as part of the bulk operation
        :raises ValueError: if the provided document instance is already part of the bulk operation
        :return: the provided document
        """
        return self.append(doc)

    def append(self, doc: Document) -> Document:
        """Add a document to this bulk operation.

        :param doc: the document that should be stored as part of the bulk operation
        :raises ValueError: if the provided document instance is already part of the bulk operation
        :return: the provided document
        """
        if any(doc.id == d.id for d in self._docs):
            raise ValueError(
                f"There is already another Document instance for {doc.id} part of the BulkOperation"
            )

        self._docs.append(doc)
        return doc


class BulkCreateOperation(BulkOperation):
    """A context manager for bulk creation operations. This operation allows to
    write many documents in one request.

    Bulk operations use the :ref:`_bulk_docs<couchdb:api/db/bulk_docs>`
    endpoint of the database.

    :param database: The database used in the bulk operation
    :param ids: a list of ids of the involved documents, defaults to []
    """

    def __init__(self, database: "database.Database", ids: List[str] = []):
        super().__init__(database=database)
        self._ids = ids

    async def __aenter__(self) -> "BulkCreateOperation":
        self._docs.extend([Document(self._database, id) for id in self._ids])
        return self


class BulkUpdateOperation(BulkOperation):
    """A context manager for bulk update of documents. In particular, for every provided
    id, a :class:`~aiocouch.document.Document` instance is provided. The data is fetched
    using the :class:`~aiocouch.view.AllDocsView` with a minimal amount of requests.

    :param database: The database of the bulk operation
    :param ids: list of document ids
    :param create: If ``True``, every document contained in `ids` that doesn't
            exist, will be represented by an empty
            :class:`~aiocouch.document.Document` instance.
    """

    def __init__(
        self, database: "database.Database", ids: List[str] = [], create: bool = False
    ):
        super().__init__(database=database)
        self._ids = ids
        self._create = create

    async def __aenter__(self) -> "BulkUpdateOperation":
        self._docs.extend(
            [doc async for doc in self._database.docs(self._ids, create=self._create)]
        )
        return self
