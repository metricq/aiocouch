import aiohttp

from contextlib import suppress
import functools


class BadRequestError(ValueError):
    pass


class UnauthorizedError(PermissionError):
    pass


class ForbiddenError(PermissionError):
    pass


class NotFoundError(KeyError):
    pass


class ConflictError(KeyError):
    pass


class ExpectationFailedError(ValueError):
    pass


class PreconditionFailedError(RuntimeError):
    pass


class UnsupportedMediaTypeError(ValueError):
    pass


def raise_for_endpoint(endpoint, message, exception, exception_type=None):
    if exception_type is None:
        if exception.status == 400:
            exception_type = BadRequestError
        elif exception.status == 401:
            exception_type = UnauthorizedError
        elif exception.status == 403:
            exception_type = ForbiddenError
        elif exception.status == 404:
            exception_type = NotFoundError
        elif exception.status == 409:
            exception_type = ConflictError
        elif exception.status == 412:
            exception_type = PreconditionFailedError
        elif exception.status == 415:
            exception_type = UnsupportedMediaTypeError
        elif exception.status == 417:
            exception_type = ExpectationFailedError
        else:
            raise ValueError(
                "Something went wrong, but I couldn't deduce the type of exception nor "
                "format a nice exception for you. I'm sorry."
            ) from exception

    message_input = {}

    with suppress(KeyError, AttributeError):
        message_input["id"] = endpoint.id
        message_input["endpoint"] = endpoint.endpoint
        message_input["rev"] = endpoint._data["_rev"]

    raise exception_type(message.format(**message_input)) from exception


def raises(status, message, exception_type=None):
    def decorator_raises(func):
        @functools.wraps(func)
        async def wrapper(endpoint, *args, **kwargs):
            try:
                return await func(endpoint, *args, **kwargs)
            except aiohttp.ClientResponseError as exception:
                if status == exception.status:
                    raise_for_endpoint(endpoint, message, exception, exception_type)
                raise exception

        return wrapper

    return decorator_raises
