# Copyright (c) 2020, ZIH,
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

from typing import Any, AsyncGenerator, Dict, Optional, cast

from . import database
from .document import Document


class FindRequestChunk:
    def __init__(
        self,
        database: "database.Database",
        *,
        data: Dict[str, Any],
        pagination_size: int,
    ):
        self.database = database
        self.data = data
        self.pagination_size = pagination_size

    @property
    async def docs(self) -> AsyncGenerator[Document, None]:
        for res in self.data["docs"]:
            doc = Document(self.database, res["_id"])
            doc._update_cache(res)
            yield doc

    @property
    def bookmark(self) -> str:
        return cast(str, self.data["bookmark"])

    @property
    def is_last_chunk(self) -> bool:
        return len(self.data["docs"]) < self.pagination_size


class FindRequest:
    def __init__(
        self,
        database: "database.Database",
        selector: Any,
        *,
        limit: Optional[int] = None,
        **params: Any,
    ):
        self.database = database
        self.selector = selector
        self.limit = limit
        self.params = params

    async def __aiter__(self) -> AsyncGenerator[Document, None]:
        pagination_size = self.limit if self.limit is not None else 10000

        while True:
            chunk = FindRequestChunk(
                self.database,
                data=await self.database._find(
                    self.selector,
                    limit=pagination_size,
                    **self.params,
                ),
                pagination_size=pagination_size,
            )

            self.params["bookmark"] = chunk.bookmark

            async for doc in chunk.docs:
                yield doc

            if self.limit is not None or chunk.is_last_chunk:
                break
