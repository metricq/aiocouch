Documents
=========

A key role in *aiocouch* takes the :class:`~aiocouch.document.Document` class. Every data send and
retrieved from the server is represented by an instance of that class.

While the constructor can be used to get an instance representing a specific document, the canonical
way is the usage of member functions of instances of the :class:`~aiocouch.database.Database` class.


Examples
--------




Reference
---------

.. autoclass:: aiocouch.document.Document
    :members:
