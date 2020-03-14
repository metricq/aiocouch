import asyncio
import timeit

from aiocouch import CouchDB


async def main_with():
    async with CouchDB(
        "http://localhost:5984", user="admin", password="admin"
    ) as couchdb:

        database = await couchdb["unfun"]

        # selector = {
        #     "_id": {
        #      "$regex": "^taurus\\.taurusi5172.*$"
        #     }
        # }
        #
        # async for doc in database.find(selector=selector):
        #     print(doc)

        # async for doc in database.docs():
        #     if doc.id.startswith("taurus.taurusi5172."):
        #         print(doc)

        # async for doc in database.docs(prefix="taurus.taurusi5172."):
        #     print(doc)

        async for key in database.all_docs().akeys(prefix="x"):
            print(key)

        print("------")

        async for key in database.view("view", "new-view").akeys(prefix="x"):
            print(key)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    repeat = 10

    print(
        timeit.timeit(lambda: loop.run_until_complete(main_with()), number=repeat)
        / repeat
    )

    # loop.run_until_complete(main_with())
