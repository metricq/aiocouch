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

from contextlib import suppress
from typing import (
    Any,
    AsyncContextManager,
    AsyncGenerator,
    Callable,
    List,
    Optional,
    TypeVar,
)

from . import couchdb
from .bulk import BulkCreateOperation, BulkUpdateOperation
from .design_document import DesignDocument
from .document import Document, SecurityDocument
from .event import BaseChangeEvent, ChangedEvent, DeletedEvent
from .exception import ConflictError, NotFoundError
from .remote import RemoteDatabase
from .request import FindRequest
from .typing import JsonDict
from .view import AllDocsView, View

FuncT = TypeVar("FuncT", bound=Callable[..., Any])


def _returns_async_context_manager(f: FuncT) -> FuncT:
    setattr(f, "__returns_acontextmanager__", True)
    return f


class Database(RemoteDatabase):
    """A local representation for the referenced CouchDB database

    An instance of this class represents a local copy of a CouchDB database. It allows
    to create and retrieve :class:`~aiocouch.document.Document` instances, as well as
    the iteration other many documents.

    :ivar id: the id of the database

    :param `~aiocouch.CouchDB` couchdb: The CouchDB connection session
    :param id: the id of the database

    """

    def __init__(self, couchdb: "couchdb.CouchDB", id: str):
        super().__init__(couchdb._server, id)

    async def akeys(self, **params: Any) -> AsyncGenerator[str, None]:
        """A generator returning the names of all documents in the database

        :param params: passed into :meth:`aiohttp.ClientSession.request`
        :return: returns all document ids

        """
        async for key in self.all_docs.ids(**params):
            yield key

    async def create(
        self, id: str, exists_ok: bool = False, data: Optional[JsonDict] = None
    ) -> "Document":
        """Returns a local representation of a new document in the database

        This method will check if a document with the given name already exists and
        return a :class:`~aiocouch.document.Document` instance.

        This method does not create a document with the given name on the server. You
        need to call :meth:`~aiocouch.document.Document.save` on the returned document.

        :raises ~aiocouch.ConflictError: if the document does not exist on the server

        :param id: the name of the document
        :param exists_ok: If `True`, do not raise a :class:`~aiocouch.ConflictError` if
            an document with the given name already exists. Instead return the existing
            document.
        :param data: Description of parameter `data`. Defaults to None.
        :return: returns a :class:`~aiocouch.document.Document` instance representing
            the requested document

        """
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

    async def delete(self) -> None:
        """Delete the database on the server

        Send the request to delete the database and all of its documents.

        """
        await self._delete()

    async def docs(
        self,
        ids: Optional[List[str]] = None,
        create: bool = False,
        prefix: Optional[str] = None,
        include_ddocs: bool = False,
        **params: Any,
    ) -> AsyncGenerator["Document", None]:
        """A generator to iterator over all or a subset of documents in the database.

        When neither of ``ids`` nor ``prefix`` are specified, all documents will be
        iterated. Only one of ``ids`` and ``prefix`` can be specified. By default, design
        documents are not included.

        :param ids: Allows to iterate over a subset of documents by passing a list of
            document ids
        :param create: If ``True``, every document contained in `ids`, which doesn't
            exist, will be represented by an empty
            :class:`~aiocouch.document.Document` instance.
        :param prefix: Allows to iterator over a subset of documents by specifing a
            prefix that the documents must match.
        :param include_ddocs: Include the design documents of the database.
        :param params: Additional query parameters,
            see :ref:`CouchDB view endpoint <couchdb:api/ddoc/view>`.

        """
        if ids is not None and len(ids) == 0:
            return

        async for doc in self.all_docs.docs(
            ids, create, prefix, include_ddocs, **params
        ):
            yield doc

    async def values(self, **params: Any) -> AsyncGenerator["Document", None]:
        """Iterates over documents in the database

        See :meth:`~aiocouch.database.Database.docs`.
        """
        async for doc in self.all_docs.docs(**params):
            yield doc

    @property
    def all_docs(self) -> AllDocsView:
        """Returns the all_docs view of the database

        :return: Description of returned object.

        """
        return AllDocsView(self)

    def view(self, design_doc: str, view: str) -> View:
        return View(self, design_doc, view)

    async def design_doc(self, id: str, exists_ok: bool = False) -> DesignDocument:
        ddoc = DesignDocument(self, id)

        if exists_ok:
            with suppress(NotFoundError):
                await ddoc.fetch(discard_changes=True)
        else:
            if await ddoc._exists():
                raise ConflictError(
                    f"The design document '{id}' does already exist in the database '{self.id}'"
                )

        return ddoc

    async def find(
        self, selector: Any, limit: Optional[int] = None, **params: Any
    ) -> AsyncGenerator["Document", None]:
        """Fetch documents based on search criteria

        This method allows to use the :ref:`_find<couchdb:api/db/_find>`
        endpoint of the database.

        This method supports all request paramters listed in
        :ref:`_find<couchdb:api/db/_find>`.

        .. note:: As this method returns :class:`~aiocouch.document.Document` s, which
            contain the complete data, the `fields` parameter is not supported.

        :param type selector: See :ref:`selectors<couchdb:find/selectors>`
        :return: return all documents matching the passed selector.
        """

        # we need to get the complete doc, so fields selector isn't allowed
        if "fields" in params.keys():
            raise ValueError("The fields parameter isn't supported")

        async for doc in FindRequest(self, selector, limit, **params):
            yield doc

    async def index(self, index: JsonDict, **kwargs: Any) -> JsonDict:
        """Create a new index on the database

        This method allows to use the :ref:`_index<couchdb:api/db/find/index>`
        endpoint of the database.

        This method supports all request paramters listed in
        :ref:`_index<couchdb:api/db/find/index>`.

        :param index: JSON description of the index
        :param kwargs: additional parameters, refer to the CouchDB documentation
        :return: The response of the CouchDB _index endpoint
        """
        return await self._index(index, **kwargs)

    @_returns_async_context_manager
    def update_docs(
        self, ids: List[str] = [], create: bool = False
    ) -> AsyncContextManager[BulkUpdateOperation]:
        """Update documents in bulk.

        See :ref:`bulk operations`.

        :param ids: list of affected documents, defaults to []
        :param create: [description], defaults to False
        :return: A context manager for the bulk operation

        """

        return BulkUpdateOperation(self, ids, create)

    @_returns_async_context_manager
    def create_docs(
        self, ids: List[str] = []
    ) -> AsyncContextManager[BulkCreateOperation]:
        """Create documents in bulk.

        See :ref:`bulk operations`.

        :param ids: list of document ids to be created
        :return: A context manager for the bulk operation

        """

        return BulkCreateOperation(self, ids)

    async def __getitem__(self, id: str) -> Document:
        """Returns the document with the given id

        :raises `~aiocouch.NotFoundError`: if the given document does not exist

        :param id: the name of the document
        :return: a local copy of the document

        """
        return await self.get(id)

    async def get(
        self, id: str, default: Optional[JsonDict] = None, *, rev: Optional[str] = None
    ) -> Document:
        """Returns the document with the given id

        :raises `~aiocouch.NotFoundError`: if the given document does not exist and
            `default` is `None`
        :raises `~aiocouch.BadRequestError`: if the given rev of the document is
            invalid or missing


        :param id: the name of the document
        :param default: if `default` is not `None` and the document does not exist on
            the server, a new :class:`~aiocouch.document.Document` instance, containing
            `default` as its contents, is returned. To create the document on the
            server, :meth:`~aiocouch.document.Document.save` has to be called on the
            returned instance.
        :param rev: The requested rev of the document. The requested rev might not
            or not anymore exist on the connected server.
        :return: a local representation of the requested document

        """
        doc = Document(self, id, data=default)

        try:
            await doc.fetch(discard_changes=True, rev=rev)
        except NotFoundError as e:
            if default is None:
                raise e

        return doc

    async def security(self) -> SecurityDocument:
        doc = SecurityDocument(self)
        await doc.fetch(discard_changes=True)
        return doc

    async def info(self) -> JsonDict:
        """Returns basic information about the database

        See also :ref:`GET /db<couchdb:api/db>`.

        :return: Description of returned object.
        :rtype: def

        """
        return await self._get()

    async def changes(self, **params: Any) -> AsyncGenerator[BaseChangeEvent, None]:
        params["feed"] = "continuous"
        params.setdefault("since", "now")
        params.setdefault("heartbeat", True)
        async for json in self._changes(**params):
            if "deleted" in json and json["deleted"] is True:
                yield DeletedEvent(
                    id=json["id"], rev=json["changes"][0]["rev"], json=json
                )
            else:
                yield ChangedEvent(
                    database=self,
                    id=json["id"],
                    rev=json["changes"][0]["rev"],
                    json=json,
                )
