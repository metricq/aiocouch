import asyncio
from typing import Any, cast

import pytest

from aiocouch.database import Database
from aiocouch.document import Document
from aiocouch.event import BaseChangeEvent, ChangedEvent, DeletedEvent

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def listen_for_first_change(database: Database, **kwargs: Any) -> BaseChangeEvent:
    async for event in database.changes(**kwargs, feed="continuous", since="now"):
        return event

    assert False


async def test_changed_event_for_new_document(database: Database) -> None:
    async def create_doc(database: Database) -> Document:
        await asyncio.sleep(0.1)
        doc = await database.create("foo", data={"Zebras": "are pants"})
        await doc.save()

        return doc

    results = await asyncio.gather(
        listen_for_first_change(database), create_doc(database)
    )

    event = results[0]
    doc = results[1]

    assert isinstance(event, ChangedEvent)
    assert event.id == "foo"
    assert event.rev == doc.rev

    doc2 = await event.doc()
    assert doc2.id == "foo"
    assert doc2.rev == event.rev
    assert "Zebras" in doc2


async def test_changed_event_for_existing_doc(filled_database: Database) -> None:
    async def update_doc(doc: Document) -> None:
        await asyncio.sleep(0.1)
        doc["Zebras"] = "are black with white stripes"
        await doc.save()

    doc = await filled_database["foo"]

    results = await asyncio.gather(
        listen_for_first_change(filled_database), update_doc(doc)
    )

    event = results[0]

    assert isinstance(event, ChangedEvent)
    assert event.id == "foo"
    assert event.rev == doc.rev

    doc2 = await event.doc()
    assert doc2.id == "foo"
    assert doc2.rev == event.rev
    assert "Zebras" in doc2


async def test_deleted_event(filled_database: Database) -> None:
    async def delete_doc(doc: Document) -> None:
        await asyncio.sleep(0.1)

        await doc.delete()

    doc = await filled_database["foo"]

    results = await asyncio.gather(
        listen_for_first_change(filled_database), delete_doc(doc)
    )

    event = results[0]

    assert isinstance(event, DeletedEvent)
    assert event.id == "foo"
    assert event.rev.startswith("2-e3a")


async def test_changed_event_not_include_docs(filled_database: Database) -> None:
    async def update_doc(doc: Document) -> None:
        await asyncio.sleep(0.1)
        doc["Zebras"] = "are black with white stripes"
        await doc.save()

    doc = await filled_database["foo"]

    results = await asyncio.gather(
        listen_for_first_change(filled_database), update_doc(doc)
    )

    event = results[0]

    assert isinstance(event, ChangedEvent)
    assert event.id == "foo"
    assert event.rev == doc.rev

    doc2 = await event.doc()

    assert doc2.id == "foo"
    assert doc2.rev == event.rev
    assert "Zebras" in doc2
    assert doc2["Zebras"] == "are black with white stripes"

    # DO NOT DO THIS, EVIL INTERAL HACK DONE FOR TESTING ONLY
    event.database = cast(Database, None)

    # As we set the database to None, it either gets the Document instance
    # from the local json response, or fails trying to gather it from the remote
    with pytest.raises(AttributeError):
        await event.doc()


async def test_changed_event_include_docs(filled_database: Database) -> None:
    async def update_doc(doc: Document) -> None:
        await asyncio.sleep(0.1)
        doc["Zebras"] = "are black with white stripes"
        await doc.save()

    doc = await filled_database["foo"]

    results = await asyncio.gather(
        listen_for_first_change(filled_database, include_docs=True), update_doc(doc)
    )

    event = results[0]

    assert isinstance(event, ChangedEvent)
    assert event.id == "foo"
    assert event.rev == doc.rev

    assert "doc" in event.json

    doc2 = await event.doc()

    assert doc2.id == "foo"
    assert doc2.rev == event.rev
    assert "Zebras" in doc2
    assert doc2["Zebras"] == "are black with white stripes"

    # DO NOT DO THIS, EVIL INTERAL HACK DONE FOR TESTING ONLY
    event.database = cast(Database, None)

    # As we set the database to None, it either gets the Document instance
    # from the local json response, or fails trying to gather it from the remote
    await event.doc()
