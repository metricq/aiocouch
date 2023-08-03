import asyncio
import uuid

from aiocouch import CouchDB
from aiocouch.event import ChangedEvent, DeletedEvent


async def main_with() -> None:
    async with CouchDB(
        "http://localhost:5984", user="admin", password="admin"
    ) as couchdb:
        database = await couchdb["test"]

        async for event in database.changes(include_docs=True):
            if isinstance(event, DeletedEvent):
                print(f"The document {event.id} was deleted.")
            elif isinstance(event, ChangedEvent):
                print(f"The document {event.id} was saved as {event.rev}")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_with())
