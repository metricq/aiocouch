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

from typing import Any, Optional

from .document import Document
from .exception import ConflictError
from .remote import _quote_id
from .view import View


class DesignDocument(Document):
    _allowed_keys = [
        "language",
        "options",
        "filters",
        "lists",
        "rewrites",
        "shows",
        "updates",
        "validate_doc_update",
        "views",
    ]

    @property
    def endpoint(self) -> str:
        return f"{self._database.endpoint}/_design/{_quote_id(self.id)}"

    def __setitem__(self, key: str, value: Any) -> None:
        if key in self._allowed_keys:
            super().__setitem__(key, value)
        else:
            raise KeyError(f"The key '{key}' is not allowed in an design document.")

    def view(self, view: str) -> View:
        return View(self._database, self.id, view)

    async def create_view(
        self,
        view: str,
        map_function: str,
        reduce_function: Optional[str] = None,
        *,
        exists_ok: bool = False,
    ) -> View:
        if "views" not in self:
            self["views"] = {}

        if view in self["views"] and not exists_ok:
            raise ConflictError(
                f"The view '{view}' does already exist in the design document {self.id}"
            )

        self["views"][view] = {"map": map_function}
        if reduce_function is not None:
            self["views"][view]["reduce"] = reduce_function
        self["language"] = "javascript"

        await self.save()

        return self.view(view)
