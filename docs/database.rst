=========
Databases
=========

Once you have established a session with the server, you need a :class:`~aiocouch.database.Database`
instance to access the data. A Database instance is an representation of a database on the server.
Database instances allow to access :class:`~aiocouch.document.Document` instances. Also, Database
instances can be used to configure the user and group permissions.


Getting a Database instance
===========================

While the constructor of the :class:`~aiocouch.database.Database` class can be used to get a
representation of a specific database, the canonical way to get an instance are the member functions
of the :class:`~aiocouch.CouchDB` class.

The following code returns an instance for the `animals` database.

.. code-block :: python

    animals = await session["animals"]

`aiocouch` only allows to get an instance for a database that exists on the server.


Creating new databases
=======================

To create a new database on the server, the :meth:`~aiocouch.CouchDB.create` method of the
session object is used.

.. code-block :: python

    animals = await session.create("animals")

By default, `aiocouch` only allows to use the create method for a database that does not exist on
the server.


Listing documents
=================

The :ref:`_all_docs<couchdb:api/db/all_docs>` view allows to retrieve all documents stored in a
given database on the server. `aiocouch` also exposes this view as methods of the database class.

The method :meth:`~aiocouch.database.Database.docs` allows to retrieve documents by a list of ids
or all documents with ids matching a given prefix. Similar to a dict, all documents of a database
can be iterated with the methods :meth:`~aiocouch.database.Database.akeys`, and
:meth:`~aiocouch.database.Database.values`.

To perform more sophisticated document selections, the method
:meth:`~aiocouch.database.Database.find` allows to search for documents matching the complex
:ref:`selector syntax<couchdb:find/selectors>` of CouchDB.

Reference
=========

.. autoclass:: aiocouch.database.Database
    :members:
    :special-members: __getitem__

.. autoclass:: aiocouch.event.BaseChangeEvent
    :members:

.. autoclass:: aiocouch.event.ChangedEvent
    :members:

.. autoclass:: aiocouch.event.DeletedEvent
    :members:
