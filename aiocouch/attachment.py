# Copyright (c) 2020, Adrien Vergé
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

from typing import cast

from .remote import RemoteAttachment


class Attachment(RemoteAttachment):
    """A local representation for the referenced CouchDB document attachment

    An instance of this class represents a local copy of an attachment of CouchDB
    documents.

    :ivar id: the id of the attachment
    :ivar content_type: the content type of the attachment, only available after
        :meth:`~aiocouch.attachment.Attachment.fetch()` has been called.

    :param `~aiocouch.document.Document` document: The correlated document
    :param id: the id of the attachment

    """

    async def exists(self) -> bool:
        """Checks if the attachment exists on the server

        :return: returns True if the attachment exists
        """
        return await self._exists()

    async def fetch(self) -> bytes:
        """Returns the content of the attachment

        :return: the attachment content

        """
        return await self._get()

    async def save(self, data: bytes, content_type: str) -> None:
        """Saves the given attachment content on the server

        :param data: the content of the attachment
        :param content_type: the content type of the given data. (See
            `Content type <https://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.17>`_)

        """
        await self._put(await self._get_doc_rev(), data, content_type)
        # Parent document needs to have '_attachments' and '_rev' updated:
        await self._document.fetch()

    async def delete(self) -> None:
        """Deletes the attachment from the server"""
        await self._delete(await self._get_doc_rev())
        # Parent document needs to have '_attachments' and '_rev' updated
        await self._document.fetch()

    async def _get_doc_rev(self) -> str:
        if not self._document.exists:
            raise ValueError(
                "The document must be fetched or saved before updating attachments"
            )

        return cast(str, self._document["_rev"])
