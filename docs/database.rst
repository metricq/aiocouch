=========
Databases
=========

Once you have established a session with the server, you need a :class:`~aiocouch.database.Database`
instance. A Database stores many :class:`~aiocouch.document.Document` s. Also, Documents are used
for user authorization.

Getting a Database instance
===========================

While the constructor can be used to get an instance representing a specific database, the canonical
way is to use member functions of the :class:`~aiocouch.couchdb.CouchDB` class.

The following code returns an instance for the `animals` database.

.. code-block :: python

    animals = await session["animals"]


Reference
=========

.. autoclass:: aiocouch.database.Database
    :members:
    :special-members: __getitem__
