.. _bulk operations:

===============
Bulk operations
===============

Bulk operations are helpful when you need to create or update several documents
within one :class:`~aiocouch.database.Database` with a low amount of requests.
In particular, the :ref:`_bulk_docs<couchdb:api/db/bulk_docs>` endpoint allows
to write a bunch of documents in one request.

Bulk operations in `aiocouch` are similar to transactions. You define the set
of affected :class:`~aiocouch.document.Document`, apply the changes and
finally perform the bulk request. Depending on the particular task, you 
need to use one of two context manager classes.

For example, the following code affects the documents `foo` and `baz`, existing or not,
and sets the key `llama` to `awesome` with one bulk request.

.. code-block :: python

    async with database.update_docs(["foo", "baz"], create=True) as docs:
        async for doc in docs:
            doc["llama"] = "awesome"

Include documents in bulk operations
====================================

Affected documents can be defined in two ways. The first way is to pass a list of
document ids as the `ids` parameter.

.. code-block :: python

    async with database.update_docs(ids=["foo", "baz"]) as docs:
        ...

The second method is the usage of the :meth:`~aiocouch.bulk.BulkOperation.append` method.
Just pass an instance of :class:`~aiocouch.document.Document` and its content will be saved
as part of the bulk operation.

.. code-block :: python

    the_document = Document(...)

    async with BulkOperation(database=my_database) as docs:
        docs.append(the_document)
    
    
Once the control flow leaves the context, the bulk operation persists the applied changes to
all documents that there included in the bulk operation one or the other way. Also,
both ways can be mixed.


Create many documents in one operation
======================================


Update many documents in one operation
======================================


Error handling for bulk operations
==================================

The important bit first, none of the bulk operation context manager will raise an exception
if something in the request went wrong. Each individual document can be saved successfully
or may have an error. It's in your responsibility to check the status after the request
finished.

You can check the status of each document with the `ok`, `error` and `status` properties
of the context manager. The `status` contains the response from the CouchDB server.
So in case of an error, there will be a description for what went wrong.

.. code-block :: python

    async with BulkOperation(database=my_database) as docs:
        ...

    if len(docs.error) == 0:
        print(f"Saved all {len(docs.ok)} documents")
    else:
        print(f"Failed to saved {len(docs.error)} documents")


Reference
=========

.. autoclass:: aiocouch.bulk.BulkOperation
    :members:
    :special-members: __aiter__

.. autoclass:: aiocouch.bulk.BulkCreateOperation
    :members:


.. autoclass:: aiocouch.bulk.BulkUpdateOperation
    :members:
