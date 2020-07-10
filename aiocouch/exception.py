# Copyright (c) 2019, ZIH,
# Technische Universitaet Dresden,
# Federal Republic of Germany
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.
#     * Neither the name of metricq nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import aiohttp

from contextlib import suppress
import functools


class BadRequestError(ValueError):
    """Represents a 400 HTTP status code returned from the server"""

    pass


class UnauthorizedError(PermissionError):
    """Represents a 401 HTTP status code returned from the server"""

    pass


class ForbiddenError(PermissionError):
    """Represents a 403 HTTP status code returned from the server"""

    pass


class NotFoundError(KeyError):
    """Represents a 404 HTTP status code returned from the server"""

    pass


class ConflictError(KeyError):
    """Represents a 409 HTTP status code returned from the server"""

    pass


class PreconditionFailedError(ValueError):
    """Represents a 412 HTTP status code returned from the server"""

    pass


class UnsupportedMediaTypeError(ValueError):
    """Represents a 415 HTTP status code returned from the server"""

    pass


class ExpectationFailedError(ValueError):
    """Represents a 417 HTTP status code returned from the server"""

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

    with suppress(AttributeError):
        message_input["id"] = endpoint.id
        message_input["endpoint"] = endpoint.endpoint
        message_input["rev"] = endpoint._data.get("_rev")
    with suppress(AttributeError):
        message_input["document_id"] = endpoint._document.id
        message_input["document_rev"] = endpoint._document._data.get("_rev")

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
