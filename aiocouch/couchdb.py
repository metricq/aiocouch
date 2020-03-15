from .remote import RemoteServer
from .database import Database
from .exception import UnauthorizedError


class CouchDB(object):
    def __init__(self, *args, **kwargs):
        self._server = RemoteServer(*args, **kwargs)

    async def __aenter__(self):
        try:
            await self.check_credentials()
        except UnauthorizedError as e:
            await self.close()
            raise e
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    async def check_credentials(self):
        await self._server._check_session()

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
