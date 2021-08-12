===============
Bulk operations
===============

Bulk operations are helpful when you need to create or update several documents
within one :class:`~aiocouch.database.Database` with a low amount of requests.
In particular, the :ref:`_bulk_docs<couchdb:api/db/bulk_docs>` endpoint allows
to write a bunch of documents in one request.

Bulk operations in `aiocouch` are similar to transactions. Depending on the
particular task, you need to use one of two context manager classes.

Include documents in bulk operations
====================================



Update documents in one operation
=================================



Reference
=========

.. autoclass:: aiocouch.bulk.BulkStoreOperation
    :members:
    :special-members: __aiter__

.. autoclass:: aiocouch.bulk.BulkUpdateOperation
    :members:
