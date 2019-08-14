from .document import Document
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
    def endpoint(self):
        return f"{self._database.endpoint}/_design/{_quote_id(self.id)}"

    def __setitem__(self, key, value):
        if key in self._allowed_keys:
            super().__setitem__(key, value)
        else:
            raise KeyError(f"The key '{key}' is not allowed in an design document.")

    def view(self, view):
        return View(self._database, self.id, view)

    async def create_view(
        self, view, map_function, reduce_function=None, exists_ok=False
    ):
        if "views" not in self:
            self["views"] = {}

        if view in self["views"] and not exists_ok:
            raise KeyError(
                f"The view '{view}' does already exist in the design document {self.id}"
            )

        self["views"][view] = {"map": map_function}
        if reduce_function is not None:
            self["views"][view]["reduce"] = reduce_function
        self["language"] = "javascript"

        await self.save()

        return self.view(view)
