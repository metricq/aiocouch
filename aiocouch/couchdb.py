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

from .exception import PreconditionFailedError, NotFoundError
from .database import Database
from .remote import RemoteServer


class CouchDB(object):
    """CouchDB Server Connection Session

    The

    :param str server: URL of the CouchDB server
    :param str user: user used for authentication
    :param str password: password for authentication
    :param str cookie: The session cookie used for authentication
    :param Any kwargs: Any other kwargs are passed to :class:`aiohttp.ClientSession`

    """

    def __init__(self, *args, **kwargs):
        self._server = RemoteServer(*args, **kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    async def check_credentials(self):
        """Check the provided credentials.

            :raises ~aiocouch.UnauthorizedError: if provided credentials aren't valid

        """
        await self._server._check_session()

    async def close(self):
        """Closes the connection to the CouchDB server

        """
        await self._server.close()

    async def create(self, id: str, exists_ok: bool = False, **kwargs) -> "Database":
        """Create a new database

        :raises ~aiocouch.PreconditionFailedError: if the database already
            exists and ``exists_ok`` is ``False``

        :param id: the identifier of the database
        :param exists_ok: If ``True``, don't raise if the database exists
        :return: Returns a representation f the created database

        """
        db = Database(self, id)
        if not await db._exists():
            await db._put(**kwargs)
            return db
        elif exists_ok:
            return db
        else:
            raise PreconditionFailedError(f"The database '{id}' does already exist.")

    async def __getitem__(self, id: str) -> "Database":
        """Returns a representation for the given database identifier

        :raises ~aiocouch.NotFoundError: if the database does not exists

        :param id: The identifier of the database
        :return: The representation of the database

        """
        db = Database(self, id)

        if not await db._exists():
            raise NotFoundError(f"The database '{id}' does not exist.")

        return db

    async def keys(self, **params) -> list:
        """Returns all database names

        :return: A list containing the names of all databases on the server

        """
        return await self._server._all_dbs(**params)

    async def info(self) -> dict:
        """Returns the meta information about the connected CouchDB server.

        See also :ref:`GET /<couchdb:api/server/root>`

        :return: A dict containing the response json.

        """
        return await self._server._info()
