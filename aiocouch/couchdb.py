from .remote import RemoteServer
from .database import Database


class CouchDB(object):
    def __init__(self, *args, **kwargs):
        self._server = RemoteServer(*args, **kwargs)
        self._database_cache = {}

    async def __aenter__(self):
        await self._server._session()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    async def close(self):
        await self._server.close()

    async def get_database(self, name, **kwargs):
        if name not in self._database_cache:
            self._database_cache[name] = Database(self, name)

        db = self._database_cache[name]

        if not await db._exists():
            await db._put(**kwargs)

        return db

    async def list_databases(self, **params):
        return await self._server._all_dbs(**params)
