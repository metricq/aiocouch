from .remote import RemoteAllDocsView
from .document import Document


class AllDocsView(RemoteAllDocsView):
    def __init__(self, database):
        super().__init__(database)

    async def get(self, limit=250, sorted=False, **params):
        if limit:
            params["limit"] = limit + 1

        startkey = None
        startkey_docid = None

        while True:
            result_chunk = await self._get(
                startkey=startkey,
                startkey_docid=startkey_docid,
                sorted=sorted,
                include_docs=True,
                **params,
            )

            num_rows = min(limit, len(result_chunk["rows"]))

            for index in range(num_rows):
                res = result_chunk["rows"][index]

                doc = Document(self._database, res["id"])
                doc._update_cache(res["doc"])
                yield doc

            if len(result_chunk["rows"]) < limit + 1:
                break

            next_row = result_chunk["rows"][limit]
            startkey = f'"{next_row["key"]}"'
            startkey_docid = f'"{next_row["id"]}"'

    async def post(self, ids, sorted=False, create=False, **params):
        result_chunk = await self._post(
            ids, sorted=sorted, include_docs=True, limit=None, **params
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
