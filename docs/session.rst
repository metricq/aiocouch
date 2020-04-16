Session
=======

Every request to the CouchDB server is embedded into a session. A session is represented by an
instance of :class:`aiocouch.CouchDB`. A session can be created using the constructor of the class
or by using the class as a context manager.

Examples
--------

Create a session with the context manager

.. code-block :: python

    with aiocouch.CouchDB("http://localhost") as couchdb:
        await couchdb.check_credentials()

Note that the session will be closed, once the scope of the with statement is left.

A session can also be handled using variables. The session needs to be closed manually.

.. code-block :: python

    couchdb = aiocouch.CouchDB("http://localhost")
    await couchdb.check_credentials()
    await couchdb.close()


Reference
---------

.. autoclass:: aiocouch.CouchDB
    :members:
