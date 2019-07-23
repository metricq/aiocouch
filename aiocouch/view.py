from .remote import RemoteAllDocsView
from .document import Document


class AllDocsView(RemoteAllDocsView):
    def __init__(self, database):
        super().__init__(database)

    async def get(self, **params):
        result_chunk = await self._get(
            include_docs=True,
            **params,
        )

        for res in result_chunk["rows"]:
            doc = Document(self._database, res["id"])
            doc._update_cache(res["doc"])
            yield doc

    async def post(self, ids, create=False, **params):
        result_chunk = await self._post(
            ids, include_docs=True, **params
        )

        for res in result_chunk["rows"]:
            doc = Document(self._database, res["key"])

            if "error" not in res and "deleted" not in res["value"]:
                doc._update_cache(res["doc"])
                yield doc
            elif create:
                yield doc
            else:
                raise KeyError(
                    f"The document '{doc.id}' does not exist in the database {self._database.id}."
                )
