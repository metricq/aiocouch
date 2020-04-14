import asyncio

from aiocouch import CouchDB


async def main_with():
    async with CouchDB(
        "http://localhost:5984", user="admin", password="admin"
    ) as couchdb:
        db = await couchdb["recipes"]
        doc = await db["apple_pie"]
        print(doc["incredients"])

        new_doc = await db.create(
            "cookies", data={"title": "Grandma's cookies", "rating": "★★★★★"}
        )
        await new_doc.save()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_with())
