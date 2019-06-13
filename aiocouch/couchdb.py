from .remote import RemoteServer
from .database import Database


class CouchDB(object):
    def __init__(self, *args, **kwargs):
        self._server = RemoteServer(*args, **kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    async def close(self):
        await self._server.close()

    async def create(self, id, exists_ok=False, **kwargs):
        db = Database(self, id)
        if not await db._exists():
            await db._put(**kwargs)
            return db
        elif exists_ok:
            return db
        else:
            raise KeyError(f"The database '{id}' does already exist.")

    async def __getitem__(self, id):
        db = Database(self, id)

        if not await db._exists():
            raise KeyError(f"The database '{id}' does not exist.")

        return db

    async def keys(self, **params):
        return await self._server._all_dbs(**params)
