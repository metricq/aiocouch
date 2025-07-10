from typing import AsyncGenerator, NoReturn, cast

import pytest
from aiohttp.client import RequestInfo

from aiocouch.couchdb import JsonDict
from aiocouch.exception import (
    BadRequestError,
    ConflictError,
    ExpectationFailedError,
    ForbiddenError,
    NotFoundError,
    PreconditionFailedError,
    RemoteResponseError,
    UnauthorizedError,
    UnsupportedMediaTypeError,
    generator_raises,
    raises,
)

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


class CustomError(Exception):
    pass


class DummyEndpoint:
    @raises(400, "bad thing")
    async def raise_bad_request(self) -> NoReturn:
        raise RemoteResponseError(None, cast(RequestInfo, None), (), status=400)

    @raises(401, "bad thing")
    async def raise_unauthorized(self) -> NoReturn:
        raise RemoteResponseError(None, cast(RequestInfo, None), (), status=401)

    @raises(403, "Access forbidden: {reason}")
    async def raise_forbidden(self) -> NoReturn:
        raise RemoteResponseError("a reason", cast(RequestInfo, None), (), status=403)

    @raises(403, "Access forbidden: None")
    async def raise_forbidden_without_reason(self) -> NoReturn:
        raise RemoteResponseError(None, cast(RequestInfo, None), (), status=403)

    @raises(404, "bad thing")
    async def raise_not_found(self) -> NoReturn:
        raise RemoteResponseError(None, cast(RequestInfo, None), (), status=404)

    @raises(409, "bad thing")
    async def raise_conflict(self) -> NoReturn:
        raise RemoteResponseError(None, cast(RequestInfo, None), (), status=409)

    @raises(412, "bad thing")
    async def raise_precondition_failed(self) -> NoReturn:
        raise RemoteResponseError(None, cast(RequestInfo, None), (), status=412)

    @raises(415, "bad thing")
    async def raise_unsupported_media(self) -> NoReturn:
        raise RemoteResponseError(None, cast(RequestInfo, None), (), status=415)

    @raises(417, "bad thing")
    async def raise_expectation_failed(self) -> NoReturn:
        raise RemoteResponseError(None, cast(RequestInfo, None), (), status=417)

    @raises(500, "bad thing", CustomError)
    async def raise_custom(self) -> NoReturn:
        raise RemoteResponseError(None, cast(RequestInfo, None), (), status=500)

    @generator_raises(400, "bad thing")
    async def raise_in_generator(self) -> AsyncGenerator[JsonDict, None]:
        raise RemoteResponseError(None, cast(RequestInfo, None), (), status=400)
        yield None


async def test_raises() -> None:
    dummy = DummyEndpoint()
    with pytest.raises(BadRequestError):
        await dummy.raise_bad_request()

    with pytest.raises(UnauthorizedError):
        await dummy.raise_unauthorized()

    with pytest.raises(ForbiddenError, match="Access forbidden: a reason"):
        await dummy.raise_forbidden()

    with pytest.raises(NotFoundError):
        await dummy.raise_not_found()

    with pytest.raises(ConflictError):
        await dummy.raise_conflict()

    with pytest.raises(PreconditionFailedError):
        await dummy.raise_precondition_failed()

    with pytest.raises(UnsupportedMediaTypeError):
        await dummy.raise_unsupported_media()

    with pytest.raises(ExpectationFailedError):
        await dummy.raise_expectation_failed()

    with pytest.raises(CustomError):
        await dummy.raise_custom()

    with pytest.raises(BadRequestError):
        async for _ in dummy.raise_in_generator():
            pass
