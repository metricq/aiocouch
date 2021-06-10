import pytest

from aiocouch import ConflictError, NotFoundError
from aiocouch.document import Document

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio

text = (
    b"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed non risus. Suspendisse "
    b"lectus tortor, dignissim sit amet, adipiscing nec, ultricies sed, dolor. Cras elementum "
    b"ultrices diam. Maecenas ligula massa, varius a, semper congue, euismod non, mi."
)

image = (
    b"RIFF\xb0\x00\x00\x00WEBPVP8 \xa4\x00\x00\x00P\x06\x00\x9d\x01*K\x002\x00?\xfd\xfe\xff"
    b"\x7f\xbf\xba\xb6\xb2>H\x03\xf0?\x89b\x00\xcc\x1c\x18\x05i\xc1\xdf\xfde\xe3\xfcr\xcb\xbb"
    b"DX^^\x9f\x9f\xcc/\xd2s]\x9a2j`\xeb\xaa@\x00\xd6\x8c\xfd;\xd5+\x9c\xb8\xb0\x9b\xabM\x07"
    b"\xc4\xd4\x07b\xcc\x1d\x13\x13\xa3\x9dR?\x9aJe\xe6\x1f\xbf\xed\x17\x19\xdc \x17\x92\xd9"
    b"\x8eR\x94\xad\x91+\xf1f@\x81\x9a\xcc{\x89\x84;\xd7\xdf\xffk\xea\xc0\xa8\xb9\xe1\xda\xea"
    b"\xe0\x07\x83\x12&\r\xae)$\x1b\xdc\xe9\xe5\xf0\xb0\xe0a\x0bP\xf1\x04iw\x03a\x86\rM\xe8"
    b"\xe9\xe0i\x08\xb1\xa0\x00\x00\x00"
)


async def test_save_text(doc: Document) -> None:
    await doc.save()
    att = doc.attachment("lipsum.txt")
    await att.save(text, "text/plain")


async def test_save_binary(doc: Document) -> None:
    await doc.save()
    att = doc.attachment("image.webp")
    await att.save(image, "image/webp")


async def test_save_on_unfetched(doc: Document) -> None:
    await doc.save()

    new_doc = Document(doc._database, doc["_id"])

    att = new_doc.attachment("lipsum.txt")
    with pytest.raises(ValueError):
        await att.save(text, "text/plain")

    new_doc = await doc._database.get(doc["_id"])
    att = new_doc.attachment("image.webp")
    await att.save(text, "text/plain")


async def test_get(doc: Document) -> None:
    await doc.save()
    await doc.attachment("image.webp").save(image, "image/webp")

    att = doc.attachment("image.webp")
    assert await att.exists()
    data = await att.fetch()
    assert data == image
    assert att.content_type == "image/webp"


async def test_get_on_unfetched(doc: Document) -> None:
    await doc.save()
    await doc.attachment("image.webp").save(image, "image/webp")

    new_doc = Document(doc._database, doc["_id"])
    att = new_doc.attachment("image.webp")
    data = await att.fetch()
    assert data == image


async def test_update(doc: Document) -> None:
    await doc.save()

    doc["value"] = 42
    await doc.save()

    att = doc.attachment("lipsum.txt")
    await att.save(text, "text/plain")

    att = doc.attachment("image.webp")
    await att.save(image, "image/webp")

    doc["value"] = 43
    await doc.save()

    new_doc = await doc._database.get(doc["_id"])
    assert new_doc["value"] == 43
    assert await new_doc.attachment("lipsum.txt").fetch() == text
    assert await new_doc.attachment("image.webp").fetch() == image


async def test_conflict(doc: Document) -> None:
    await doc.save()

    outdated = await doc._database.get(doc["_id"])

    doc["value"] = 42
    await doc.save()

    with pytest.raises(ConflictError):
        await outdated.attachment("image.webp").save(image, "image/webp")

    await doc.attachment("image.webp").save(image, "image/webp")


async def test_conflict_on_update(doc: Document) -> None:
    await doc.save()

    outdated = await doc._database.get(doc["_id"])

    att = doc.attachment("lipsum.txt")
    await att.save(text, "text/plain")

    with pytest.raises(ConflictError):
        await outdated.attachment("image.webp").save(image, "image/webp")

    await doc.attachment("image.webp").save(image, "image/webp")


async def test_delete(doc: Document) -> None:
    await doc.save()
    att = doc.attachment("lipsum.txt")
    await att.save(text, "text/plain")

    await att.delete()

    att = doc.attachment("lipsum.txt")
    with pytest.raises(NotFoundError):
        await att.fetch()

    assert not await att.exists()
