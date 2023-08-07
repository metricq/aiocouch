import asyncio

from aiocouch import CouchDB


async def main() -> None:
    async with CouchDB(
        "http://localhost:5984", user="admin", password="admin"
    ) as couchdb:
        elapsed_time = 0

        while True:
            _, result = await couchdb._server._get("/_session")
            assert not isinstance(result, bytes)
            user = result["userCtx"]["name"]
            print(f"After {elapsed_time} sec: {user}")

            await asyncio.sleep(10)
            elapsed_time += 10


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
