===================
Welcome to aiocouch
===================

Asynchronous CouchDB client library for asyncio and Python.

Current version is |release|.

.. _GitHub: https://github.com/metricq/aiocouch

Key features
============

- All requests are asynchronus using aiohttp
- Supports CouchDB 2.x and 3.x
- Support for modern Python ≥ 3.6


Library installation
====================

..  code-block:: bash

    pip install aiocouch


Getting started
===============

The following code retrieves and prints the list of ``incredients`` of the ``apple_pie`` ``recipe``.
The ``incredients`` are stored as a list in the ``apple_pie`` :class:`~aiocouch.document.Document`,
which is part of the ``recipe`` :class:`~aiocouch.database.Database`. We use the context manager
:class:`~aiocouch.CouchDB` to create a new session.

.. code-block:: python

    from aiocouch import CouchDB

    async with CouchDB(
        "http://localhost:5984", user="admin", password="admin"
    ) as couchdb:
        db = await couchdb["recipes"]
        doc = await db["apple_pie"]
        print(doc["incredients"])

We can also create new recipes, for instance for some delicious cookies.

.. code-block:: python

        new_doc = await db.create(
            "cookies", data={"title": "Granny's cookies", "rating": "★★★★★"}
        )
        await new_doc.save()
    #


Source code
===========

The project is hosted on GitHub_.

Please feel free to file an issue on the `bug tracker
<https://github.com/metricq/aiocouch/issues>`_ if you have found a bug
or have some suggestion in order to improve the library.

The library uses `GitHub Actions <https://github.com/metricq/aiocouch/actions>`_ for
Continuous Integration.


Dependencies
============

- Python 3.6+
- *aiohttp*
- *Deprecated*


Authors and License
===================

The ``aiocouch`` package is written mostly by Mario Bielert.

It's *BSD 3-clause* licensed and freely available.

Feel free to improve this package and send a pull request to GitHub_.


Table of contents
=================

.. toctree::
   :maxdepth: 1

   session
   database
   document
   attachment
   view
   bulk
   exception

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
