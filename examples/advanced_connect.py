import asyncio

from aiocouch import CouchDB


# using the with statement, ensures a proper connection handling
async def main_with() -> None:

    # connect using username and password as credentials
    async with CouchDB(
        "http://localhost:5984", user="admin", password="admin"
    ) as couchdb:
        database = await couchdb["config"]

        async for doc in database.docs(["db-hta"]):
            print(doc)
    # connection is closed

    # connect using cookie
    async with CouchDB(
        "http://localhost:5984", cookie="ZGVtb0B0b2x0ZWNrLmNvbT..."
    ) as couchdb:
        await couchdb["_users"]
    # connection is closed


# storing the CouchDB instance allows for persistent connections
async def main_persistent() -> None:
    couchdb = CouchDB("http://localhost:5984", user="admin", password="admin")

    # optional credentials check
    await couchdb.check_credentials()

    # do something
    database = await couchdb["config"]
    async for doc in database.docs(["db-hta"]):
        print(doc)

    # close the connection without waiting
    asyncio.ensure_future(couchdb.close())

    return
    # connection is still open at this point, but will be closed soon after the return


if __name__ == "__main__":
    asyncio.run(main_with())
    asyncio.run(main_persistent())
