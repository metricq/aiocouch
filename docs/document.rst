Documents
=========

A key role in *aiocouch* takes the :class:`~aiocouch.document.Document` class. Every data send and
retrieved from the server is represented by an instance of that class. There are no other ways in
*aiocouch* to interact with documents.


Getting a Document instance
-----------------------------

While the constructor can be used to get an instance representing a specific document, the canonical
way is the usage of member functions of instances of the :class:`~aiocouch.database.Database` class.

.. code-block :: python

    butterfly_doc = await database["butterfly"]
    wolpertinger = await database.get("wolpertinger")

These methods create a :class:`~aiocouch.document.Document` and fetch the data from the server. For
some cases, though, a precise control other the performed requests are required. The above code
snippet is equivalent to this:

.. code-block :: python

    butterfly_doc = Document(database, "butterly")
    await butterfly_doc.fetch()


Creating new Documents
----------------------

The creation of a new document on the server consists of three steps. First, you need a local
document handle, i.e., an :class:`~aiocouch.document.Document` instance. Then you set the contents
of the document. And finally, the local document is saved to the server.

.. code-block :: python

    # get an Document instance
    doc = await database.create["new_doc"]

    # set the document content
    doc["name"] = "The new document"

    # actually perform the request to save the document on the server
    await doc.save()


Modify existing documents
-------------------------

The modification of an existing document works very similarly to the creation. Retrieving the
document, updating its contents, and finally saving the modified data to the server.

.. code-block :: python

    # get an Document instance
    doc = await database["existing_doc"]

    # update the document content
    doc["name"] = "The modified document"

    # actually perform the request to save the modification to the server
    await doc.save()

Conflict handling
-----------------

Whenever, two or more different :class:`~aiocouch.document.Document` instances want to save the same
document on the server, a :class:`~aiocouch.ConflictError` can occur. To cope with conflicts, there
are a set of different strategies, which can be used.

One trivial solution is to simply ignore conflicts.This is a viable strategy if only the existance
of the document matters.

.. code-block :: python

    with contextlib.suppress(aiocouch.ConflictError):
        await doc.save()

Another trivial solution is to override the contents of the existing document.

.. code-block :: python

    try:
        await doc.save()
    except aiocouch.ConflictError:
        info = await doc.info()
        doc.rev = info["rev"]
        await doc2.save()

Other applications may require a more sophisticated merging of documents. However, there isn't a
generic solution to this approach. Thus, we forego to show example code here.

Reference
---------

.. autoclass:: aiocouch.document.Document
    :members:
