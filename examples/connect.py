import asyncio

from aiocouch import CouchDB


async def main_with():
    async with CouchDB(
        "http://localhost:5984", user="admin", password="admin"
    ) as couchdb:

        print(await couchdb._server._get("/"))

        database = await couchdb.get_database("config")
        doc = await database.get("db-hta")
        print(doc)

        metadata = await couchdb.get_database("metadata")

        docs = 0
        async for doc in metadata.find({"wurst": False}):
            doc["bockmist"] = True
            docs += 1

        print(f"received {docs} docs")

        async for doc in metadata.get_all():
            doc["tummy"] = "jummy"

        await metadata.save_all()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_with())
