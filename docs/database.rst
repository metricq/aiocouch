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


Reference
=========

.. autoclass:: aiocouch.database.Database
    :members:
    :special-members: __getitem__
