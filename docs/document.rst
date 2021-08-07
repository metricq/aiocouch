=========
Documents
=========

A key role in *aiocouch* takes the :class:`~aiocouch.document.Document` class. Every data send and
retrieved from the server is represented by an instance of that class. There are no other ways in
*aiocouch* to interact with documents.


Getting a Document instance
===========================

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
======================

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
=========================

The modification of an existing document works very similarly to the creation. Retrieving the
document, updating its contents, and finally saving the modified data to the server.

.. code-block :: python

    # get an Document instance
    doc = await database["existing_doc"]

    # update the document content
    doc["name"] = "The modified document"

    # actually perform the request to save the modification to the server
    await doc.save()


Using Async Context Managers
============================

To simplify the process of retrieving a document from remote server (or creating 
a new one if it didn't exist before), modifying it, and saving changes on remote 
server, you can also use asynchronous context managers.

Using context managers saves you from having to manually perform a lot of 
these operations as the context managers handle these operations for you automatically.

**aiocouch** provides async context managers for both :class:`~aiocouch.document.Document`
and :class:`~aiocouch.document.SecurityDocument`.


Document Context Manager Example
--------------------------------

.. code-block :: python

    from aiocouch import CouchDB
    from aiocouch.document import Document

    async with CouchDB(SERVER_URL, USER, PASSWORD) as client:
        # Create database on remote server (fetching it if it already exists)
        my_database = await client.create("my_database", exists_ok=True)

        # If document exists, it's fetched from the remote server
        async with Document(my_database, "secret_agents") as document:
            # Changes are made locally
            document["name"] = "James Bond"
            document["code"] = "007"
        # Upon exit from above context manager, document is saved remotely

        # Display the newly created document after fetching from remote server
        document = await my_database["secret_agents"]
        print(document)

.. warning:: Uncaught exceptions inside the ``async with`` block will prevent your
             document changes from being saved to the remote server.


Security Document Context Manager Example
-----------------------------------------

Similarly, you can also use Security Document context manager to add or remove admins 
or members from a CouchDB database

.. code-block :: python

    from aiocouch import CouchDB
    from aiocouch.document import Document

    async with CouchDB(SERVER_URL, USER, PASSWORD) as client:
        # Create database on remote server (fetching it if it already exists)
        my_database = await client.create("my_database", exists_ok=True)

        async with SecurityDocument(my_database) as security_doc:
            # Give user 'bond' member access to 'my_database' database
            security_doc.add_member("bond")
            # Give user 'fleming' admin access to 'my_database' database
            security_doc.add_admin("fleming")
        # Upon exit from above context manager, document is saved remotely

        # Display the recent changes made to security document        
        security_doc = await my_database.security()
        print(security_doc)

.. warning:: Uncaught exceptions inside the ``async with`` block will prevent your
             security document changes from being saved to the remote server.

Conflict handling
=================

Whenever, two or more different :class:`~aiocouch.document.Document` instances want to save the same
document on the server, a :class:`~aiocouch.ConflictError` can occur. To cope with conflicts, there
are a set of different strategies, which can be used.

One trivial solution is to simply ignore conflicts.This is a viable strategy if only the existance
of the document matters.

.. code-block :: python

    with contextlib.suppress(aiocouch.ConflictError):
        await doc.save()

Another straight-forward solution is to override the contents of the existing document.

.. code-block :: python

    try:
        await doc.save()
    except aiocouch.ConflictError:
        info = await doc.info()
        doc.rev = info["rev"]
        await doc.save()

Other use cases may require a more sophisticated merging of documents. However, there isn't a
generic solution to such an approach. Thus, we forego to show example code here.

Reference
=========

.. autoclass:: aiocouch.document.Document
    :members:
