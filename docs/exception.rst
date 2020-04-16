Exceptions
==========

Most errors you encounter in aiocouch stem from HTTP request to the CouchDB server. Most of those
are therefore captured an transformed into exceptions. There might still be other errors, however
those should not be encountered under normal operation.

For further details, what can cause individual status codes, see also :ref:`HTTP Status codes  <couchdb:errors>`.

.. automodule:: aiocouch
    :members: BadRequestError, ConflictError, UnauthorizedError, ForbiddenError, NotFoundError, PreconditionFailedError, UnsupportedMediaTypeError, ExpectationFailedError
