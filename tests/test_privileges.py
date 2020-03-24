import pytest

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_security_missing_privileges(database, couchdb_with_user_access):
    from aiocouch import ForbiddenError

    sec2 = await database.security()
    sec2.add_member("aiocouch_test_user")
    await sec2.save()

    db = await couchdb_with_user_access["aiocouch_test_fixture_database"]
    sec = await db.security()

    sec.add_member("foobert")

    with pytest.raises(ForbiddenError):
        await sec.save()

    sec2.add_admin("aiocouch_test_user")
    await sec2.save()

    await sec.save()


async def test_get_missing_privileges(filled_database, couchdb_with_user_access):
    from aiocouch import ForbiddenError

    sec = await filled_database.security()
    sec.add_member("foobert")
    await sec.save()

    with pytest.raises(ForbiddenError):
        await couchdb_with_user_access["aiocouch_test_fixture_database"]


async def test_get_valid_privileges(filled_database, couchdb_with_user_access):
    from aiocouch import ForbiddenError

    sec = await filled_database.security()
    sec.add_member("aiocouch_test_user")
    await sec.save()

    database = await couchdb_with_user_access["aiocouch_test_fixture_database"]
    doc = await database["foo"]
    doc["bear"] = "brown"

    sec.remove_member("aiocouch_test_user")
    sec.add_member("foobert")
    await sec.save()

    with pytest.raises(ForbiddenError):
        await doc.save()

    with pytest.raises(ForbiddenError):
        await couchdb_with_user_access["aiocouch_test_fixture_database"]

    sec.add_member_role("aiocouch_test_role")
    await sec.save()

    database = await couchdb_with_user_access["aiocouch_test_fixture_database"]
    await database["foo"]

    await doc.save()
