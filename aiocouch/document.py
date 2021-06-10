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

import json
from contextlib import suppress
from typing import Any, Dict, ItemsView, List, Optional, cast, KeysView, ValuesView

from deprecated import deprecated

from . import database
from .attachment import Attachment
from .exception import ConflictError, ForbiddenError, raises
from .remote import RemoteDocument

JsonDict = Dict[str, Any]


class Document(RemoteDocument):
    """A local representation for the referenced CouchDB document

    An instance of this class represents a local copy of the document data on the
    server. This class behaves like a dict containing the document data and allows to
    :func:`~aiocouch.document.Document.fetch` and
    :func:`~aiocouch.document.Document.save` documents. For details about the dict-like
    interface, please refer to the :ref:`Python manual <python:typesmapping>`.

    Constructing an instance of this class does not cause any network requests.

    :ivar id: the id of the document

    :param `~aiocouch.database.Database` database: The database of the document
    :param id: the id of the document
    :param data: the inital data used to set the body of the document

    """

    def __init__(
        self, database: "database.Database", id: str, data: Optional[JsonDict] = None
    ):
        super().__init__(database, id)
        self._data: JsonDict = data if data is not None else {}
        if not isinstance(self._data, dict):
            raise TypeError("data parameter must be a dict object")
        self._data["_id"] = id
        self._data_hash: Optional[int] = None

    def _update_hash(self) -> None:
        self._data_hash = hash(json.dumps(self._data, sort_keys=True))

    @property
    def _fresh(self) -> bool:
        return len(self._data) == 1 and "_id" in self._data

    @property
    def _dirty_cache(self) -> bool:
        return self._data_hash is None or self._data_hash != hash(
            json.dumps(self._data, sort_keys=True)
        )

    async def fetch(self, discard_changes: bool = False) -> None:
        """Retrieves the document data from the server

        Fetching the document will retrieve the data from the server using a network
        request and update the local data.

        :raises ~aiocouch.ConflictError: if the local data has changed without saving

        :param discard_changes: If set to `True`, the local data object will the
            overridden with the retrieved content. If the local data was changed, no
            exception will be raised.

        """
        if self._dirty_cache and not (discard_changes or self._fresh):
            raise ConflictError(
                f"Cannot fetch document '{self.id}' from server, "
                "as the local cache has unsaved changes."
            )
        self._update_cache(await self._get())

    async def save(self) -> None:
        """Saves the current state to the CouchDB server

        :raises ~aiocouch.ConflictError: if the local revision is different from the
            server. See TODO.

        """
        if self._dirty_cache:
            data = await self._put(self._data)
            self._update_rev_after_save(data)

    async def delete(self, discard_changes: bool = False) -> None:
        """Deletes the document from the server

        Calling this method deltes the local data and the document on the server.
        Afterwards, the instance can be filled with new data and call :meth:`.save`
        again.

        :raises ~aiocouch.ConflictError: if the local data has changed without saving
        :raises ~aiocouch.ConflictError: if the local revision is different from the
            server. See TODO.

        """
        if self._dirty_cache and not discard_changes:
            raise ConflictError(
                f"Cannot delete document '{self.id}' from server, as the local cache "
                "has unsaved changes."
            )
        self._update_cache(await self._delete(rev=self["_rev"]))

    async def copy(self, new_id: str) -> "Document":
        """Create a copy of the document on the server

        Creates a new document with the data currently stored on the server.

        :param new_id: the id of the new document
        :return: an instance for the new document after it was copied

        """
        await self._copy(new_id)

        return await self._database[new_id]

    @property
    def rev(self) -> Optional[str]:
        """Allows to set and get the local revision

        If the local document wasn't fetched or saved, this is ``None``.

        """
        try:
            return cast(str, self._data["_rev"])
        except KeyError:
            return None

    @rev.setter
    def rev(self, new_rev: str) -> None:
        if not isinstance(new_rev, str):
            raise TypeError("Revision must be a string.")
        self._data["_rev"] = new_rev

    @property
    def data(self) -> Optional[JsonDict]:
        """Returns the local copy of the document as a dict

        If the document doesn't exist on the server, this function returns ``None``.

        This method does not perform a network request.

        :return: Returns the data of the document or ``None``

        """
        return self._data if self.exists else None

    @property
    def exists(self) -> bool:
        """Denotes whether the document exists

        A document exists, if it was :func:`~aiocouch.document.Document.fetch` ed from
        the server and wasn't deleted on the server.

        This method does not perform a network request.

        :return: ``True`` if the document exists, ``False`` overwise

        """
        return "_rev" in self and "_deleted" not in self

    @deprecated(
        version="1.1.0", reason="This method is a misnomer. Use info() instead."
    )
    async def fetch_info(self) -> JsonDict:
        return await self._info()

    async def info(self) -> JsonDict:
        """Returns a short information about the document.

        This method sends a request to the server to retrieve the current status.

        :raises ~aiocouch.NotFoundError: if the document does not exist on the server

        :return: A dict containing the id and revision of the document on the server

        """
        return await self._info()

    def _update_rev_after_save(self, data: JsonDict) -> None:
        with suppress(KeyError):
            self._data["_rev"] = data["rev"]
        self._update_hash()

    def _update_cache(self, new_cache: JsonDict) -> None:
        self._data = new_cache
        self._update_hash()

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def __delitem__(self, key: str) -> None:
        del self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def update(self, data: JsonDict) -> None:
        self._data.update(data)

    def items(self) -> ItemsView[str, Any]:
        return self._data.items()

    def keys(self) -> KeysView[str]:
        return self._data.keys()

    def values(self) -> ValuesView[Any]:
        return self._data.values()

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self._data.get(key, default)

    def setdefault(self, key: str, default: Optional[Any] = None) -> Any:
        return self._data.setdefault(key, default)

    def attachment(self, id: str) -> "Attachment":
        """Returns the attachment object

        The attachment object is returned, but this method doesn't actually fetch any
        data from the server. Use
        :meth:`~aiocouch.attachment.Attachment.fetch()` and
        :meth:`~aiocouch.attachment.Attachment.save()`, respectively.

        :param id: the id of the attachment
        :return: Returns the attachment object

        """
        return Attachment(self, id)

    def __repr__(self) -> str:
        return json.dumps(self._data, indent=2)


class SecurityDocument(Document):
    def __init__(self, database: "database.Database"):
        super().__init__(database, "_security")
        del self._data["_id"]

    @property
    def members(self) -> Optional[List[str]]:
        try:
            return cast(List[str], self["members"]["names"])
        except KeyError:
            return None

    @property
    def member_roles(self) -> Optional[List[str]]:
        try:
            return cast(List[str], self["members"]["roles"])
        except KeyError:
            return None

    @property
    def admins(self) -> Optional[List[str]]:
        try:
            return cast(List[str], self["admins"]["names"])
        except KeyError:
            return None

    @property
    def admin_roles(self) -> Optional[List[str]]:
        try:
            return cast(List[str], self["admins"]["roles"])
        except KeyError:
            return None

    def add_member(self, member: str) -> None:
        members = self.setdefault("members", {})
        names = members.setdefault("names", [])
        if member not in names:
            names.append(member)

    def add_member_role(self, role: str) -> None:
        members = self.setdefault("members", {})
        roles = members.setdefault("roles", [])
        if role not in roles:
            roles.append(role)

    def remove_member(self, member: str) -> None:
        try:
            self["members"]["names"].remove(member)
        except (ValueError, KeyError) as e:
            raise KeyError(
                f"The user '{member}' isn't a member of the database '{self._database.id}'"
            ) from e

    def remove_member_role(self, role: str) -> None:
        try:
            self["members"]["roles"].remove(role)
        except (ValueError, KeyError) as e:
            raise KeyError(
                f"The role '{role}' isn't a member role of the database '{self._database.id}'"
            ) from e

    def add_admin(self, admin: str) -> None:
        admins = self.setdefault("admins", {})
        names = admins.setdefault("names", [])
        if admin not in names:
            names.append(admin)

    def add_admin_role(self, role: str) -> None:
        admins = self.setdefault("admins", {})
        roles = admins.setdefault("roles", [])
        if role not in roles:
            roles.append(role)

    def remove_admin(self, admin: str) -> None:
        try:
            self["admins"]["names"].remove(admin)
        except (ValueError, KeyError) as e:
            raise KeyError(
                f"The user '{admin}' isn't an admin of the database '{self._database.id}'"
            ) from e

    def remove_admin_role(self, role: str) -> None:
        try:
            self["admins"]["roles"].remove(role)
        except (ValueError, KeyError) as e:
            raise KeyError(
                f"The role '{role}' isn't an admin role of the database '{self._database.id}'"
            ) from e

    @raises(500, "You are not a database or server admin", ForbiddenError)
    async def save(self) -> None:
        await super().save()
