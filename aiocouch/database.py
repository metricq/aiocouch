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
from .request import FindRequest
from .view import AllDocsView, View

from contextlib import suppress
from typing import List, AsyncGenerator


class Database(RemoteDatabase):
    """A local representation for the referenced CouchDB database

    An instance of this class represents a local copy of a CouchDB database. It allows
    to create and retrieve :class:`~aiocouch.document.Document` instances, as well as
    the iteration other many documents.

    :param `~aiocouch.CouchDB` couchdb: The CouchDB connection session
    :param id: the id of the database

    """

    def __init__(self, couchdb, id: str):
        super().__init__(couchdb._server, id)

    async def akeys(self, **params) -> AsyncGenerator[str, None]:
        """A generator returning the names of all documents in the database

        :param params: passed into :meth:`aiohttp.ClientSession.request`
        :return: returns all document ids

        """
        async for key in self.all_docs.ids(**params):
            yield key

    async def create(
        self, id: str, exists_ok: bool = False, data: dict = None
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

    async def delete(self):
        """Delete the database on the server

        Send the request to delete the database and all of its documents.

        """
        await self._delete()

    async def docs(
        self, ids: list = None, create: bool = False, prefix: str = None, **params
    ) -> AsyncGenerator["Document", None]:
        """A generator to iterator over all or a subset of documents in the database.

        When neither of ``ids`` nor ``prefix`` are specified, all documents will be
        iterated. Only one of ``ids`` and ``prefix`` can be specified.

        :param ids: Allows to iterate over a subset of documents by passing a list of
            document ids
        :param create: If ``True``, every document contained in `ids`, which doesn't
            exists, will be represented by an empty
            :class:`~aiocouch.document.Document` instance.
        :param  prefix: Allows to iterator over a subset of documents by specifing a
            prefix that the documents must match.
        :param params: Additional query parameters,
            see :ref:`CouchDB view endpoint <couchdb:api/ddoc/view>`.

        """
        async for doc in self.all_docs.docs(ids, create, prefix, **params):
            yield doc

    async def values(self, **params) -> AsyncGenerator["Document", None]:
        """Iterates over documents in the database

        See :meth:`~aiocouch.database.Database.docs`.
        """
        async for doc in self.all_docs.docs(**params):
            yield doc

    @property
    def all_docs(self) -> "AllDocsView":
        """Returns the all_docs view of the database

        :return: Description of returned object.

        """
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

        async for doc in FindRequest(self, selector, limit, **params):
            yield doc

    def update_docs(self, ids, create=False):
        return BulkOperation(self, ids, create)

    def create_docs(self, ids=[]):
        return BulkStoreOperation(self, ids)

    async def __getitem__(self, id: str) -> "Document":
        """Returns the document with the given id

        :raises `~aiocouch.NotFoundError`: if the given document does not exists

        :param id: the name of the document
        :return: a local copy of the document

        """
        return await self.get(id)

    async def get(self, id: str, default: dict = None):
        """Returns the document with the given id

        :raises `~aiocouch.NotFoundError`: if the given document does not exists and
            `default` is `None`


        :param id: the name of the document
        :param default: if `default` is not `None` and the document does not exists on
            the server, a new :class:`~aiocouch.document.Document` instance, containing
            `default` as its contents, is returned. To create the document on the
            server, :meth:`~aiocouch.document.Document.save` has to be called on the
            returned instance.
        :return: a local representation of the requested document

        """
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
        """Returns basic information about the database

        See also :ref:`GET /db<couchdb:api/db>`.

        :return: Description of returned object.
        :rtype: def

        """
        return await self._get()
