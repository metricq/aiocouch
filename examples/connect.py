import asyncio

from aiocouch import CouchDB


async def main_with() -> None:
    async with CouchDB(
        "http://localhost:5984", user="admin", password="admin"
    ) as couchdb:

        print((await couchdb.info())["version"])

        database = await couchdb["config"]

        async for doc in database.docs(["db-hta"]):
            print(doc)

    async with CouchDB(
        "http://localhost:5984", cookie="ZGVtb0B0b2x0ZWNrLmNvbT..."
    ) as couchdb:
        await couchdb["_users"]


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_with())
