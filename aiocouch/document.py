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

from .remote import RemoteDocument


class Document(RemoteDocument):
    def __init__(self, database, id):
        super().__init__(database, id)
        self._cached_data = {"_id": id}
        self._dirty_cache = True

    async def fetch(self, discard_changes=False):
        if self._dirty_cache and not discard_changes:
            raise ValueError(
                "Cannot fetch document from server, as the local cache has unsaved changes."
            )
        self._update_cache(await self._get())

    async def save(self):
        if self._dirty_cache:
            data = await self._put(self._cached_data)
            self._update_rev_after_save(data["rev"])

    async def delete(self, discard_changes=False):
        if self._dirty_cache and not discard_changes:
            raise ValueError(
                "Cannot fetch document from server, as the local cache has unsaved changes."
            )
        self._update_cache(await self._delete(rev=self["_rev"]))

    async def copy(self, new_id):
        await self._copy(new_id)

        return await self._database.get(new_id)

    def _update_rev_after_save(self, rev):
        self._cached_data["_rev"] = rev
        self._dirty_cache = False

    def _update_cache(self, new_cache):
        self._cached_data = new_cache
        self._dirty_cache = False

    def __getitem__(self, key):
        return self._cached_data[key]

    def __setitem__(self, key, value):
        self._dirty_cache = True
        self._cached_data[key] = value

    def __delitem__(self, key):
        self._dirty_cache = True
        del self._cached_data[key]

    def __contains__(self, key):
        return key in self._cached_data

    # TODO, do we need a del checking for dirty caches?

    def __repr__(self):
        return json.dumps(self._cached_data, indent=2)
