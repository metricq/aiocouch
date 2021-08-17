.. _bulk operations:

===============
Bulk operations
===============

Bulk operations are helpful when you need to create or update several documents within one
:class:`~aiocouch.database.Database` with a low amount of requests. In particular, the
:ref:`_bulk_docs<couchdb:api/db/bulk_docs>` endpoint allows to write a bunch of documents
in one request.

Bulk operations in `aiocouch` are similar to transactions. You define the set of affected
:class:`~aiocouch.document.Document`, apply the changes and finally perform the bulk
request. Depending on the particular task, you need to use one of two context manager
classes.

For example, the following code affects the documents `foo` and `baz`, existing or not,
and sets the key `llama` to `awesome` with one bulk request.

.. code-block :: python

    async with database.update_docs(["foo", "baz"], create=True) as bulk:
        async for doc in bulk:
            doc["llama"] = "awesome"


Include documents in bulk operations
====================================

Affected documents can be defined in two ways. The first way is to pass a list of document
ids as the `ids` parameter.

.. code-block :: python

    async with database.update_docs(ids=["foo", "baz"]) as bulk:
        ...

The second method is the usage of the :meth:`~aiocouch.bulk.BulkOperation.append` method.
Just pass an instance of :class:`~aiocouch.document.Document` and its content will be
saved as part of the bulk operation.

.. code-block :: python

    the_document = Document(...)

    async with BulkOperation(database=my_database) as bulk:
        bulk.append(the_document)

Once the control flow leaves the context, the bulk operation persists the applied changes
to all documents that there included in the bulk operation one or the other way. Also,
both ways can be mixed.


Create many documents in one operation
======================================

To create many documents, you use the :meth:`~aiocouch.database.Database.create_docs`
method to get the context manager. Include documents as described above. Once the context
manager closes, one request containing all document contents gets send to the server.

.. code-block :: python

    async with my_database.create_docs(...) as bulk:
        for doc in bulk:
            # make changes to the Document instances

    # the request was send now

Note that the bulk operation does not check, if the requested documents alrady exists on
the server. Instead, the :attr:`~aiocouch.bulk.BulkOperation.error` list will contain
`conflict` in the `error` field corresponding to the document.


Update many documents in one operation
======================================

To update many documents, you use the :meth:`~aiocouch.database.Database.update_docs`
method to get the context manager. Include documents as described above. Once the context
manager closes, one request containing all document contents gets send to the server. In
contrast to the create operation, the :class:`~aiocouch.bulk.BulkUpdateOperation` context
manager will request all documents whose ids where passed as the `ids` parameter. If you
already have :class:`~aiocouch.document.Document` instance, you may want to use the
:meth:`~aiocouch.bulk.BulkOperation.append` method instead.

.. code-block :: python

    my_doc: Document = ...

    async with my_database.update_docs(...) as bulk:
        bulk.append(my_doc)

        for doc in docs:
            # make changes to the Document instances

    # the request was send now


Error handling for bulk operations
==================================

The important bit first, none of the bulk operation context manager will raise an
exception if something in the request went wrong. Each individual document can be saved
successfully or may have an error. It's in your responsibility to check the status after
the request finished.

You can check the status of each document with the
:attr:`~aiocouch.bulk.BulkOperation.ok`, :attr:`~aiocouch.bulk.BulkOperation.error`, and
:attr:`~aiocouch.bulk.BulkOperation.response` properties of the context manager. The
:attr:`~aiocouch.bulk.BulkOperation.ok` and :attr:`~aiocouch.bulk.BulkOperation.error`
lists contain all documents that could and couldn't be saved properly, respectively. The
:attr:`~aiocouch.bulk.BulkOperation.response` contains the response from the CouchDB
server. So in case of an error, it will contain a description of what went wrong.

.. code-block :: python

    async with BulkOperation(database=my_database) as bulk:
        ...

    if len(bulk.error) == 0:
        print(f"Saved all {len(bulk.ok)} documents")
    else:
        print(f"Failed to saved {len(bulk.error)} documents")


Reference
=========

.. autoclass:: aiocouch.bulk.BulkOperation
    :members:
    :special-members: __aiter__

.. autoclass:: aiocouch.bulk.BulkCreateOperation
    :members:

.. autoclass:: aiocouch.bulk.BulkUpdateOperation
    :members:
