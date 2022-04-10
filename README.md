[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![PyPI version](https://badge.fury.io/py/aiocouch.svg)](https://badge.fury.io/py/aiocouch)
![Python package](https://github.com/metricq/aiocouch/workflows/Python%20package/badge.svg)
[![codecov](https://codecov.io/gh/metricq/aiocouch/branch/master/graph/badge.svg)](https://codecov.io/gh/metricq/aiocouch)
[![Documentation Status](https://readthedocs.org/projects/aiocouch/badge/?version=latest)](https://aiocouch.readthedocs.io/en/latest/?badge=latest)


# aiocouch
An asynchronous client library for CouchDB 2.0 based on asyncio using aiohttp

## Key features

- All requests are asynchronus using aiohttp
- Supports CouchDB 2.x and 3.x
- Support for modern Python ≥ 3.7


## Library installation

```
    pip install aiocouch
```

## Getting started

The following code retrieves and prints the list of `incredients` of the *apple_pie* `recipe`.
The `incredients` are stored as a list in the *apple_pie* `aiocouch.document.Document`,
which is part of the `recipe` `aiocouch.database.Database`. We use the context manager
`aiocouch.CouchDB` to create a new session.

```python

    from aiocouch import CouchDB

    async with CouchDB(
        "http://localhost:5984", user="admin", password="admin"
    ) as couchdb:
        db = await couchdb["recipes"]
        doc = await db["apple_pie"]
        print(doc["incredients"])
```

We can also create new recipes, for instance for some delicious cookies.

```python

        new_doc = await db.create(
            "cookies", data={"title": "Granny's cookies", "rating": "★★★★★"}
        )
        await new_doc.save()
```

For further details please refer to the documentation, which is available [here on readthedocs.org](https://aiocouch.readthedocs.io/).

## Run examples

- Setup the CouchDB URL and credentials using the environment variables
- Install dependencies using `pip install --editable '.[examples]'`
- run for instance `python examples/getting_started.py`


## Run tests

- Install dependencies using `pip install --editable '.[tests]'`
- Setup the CouchDB URL and credentials using the environment variables (`COUCHDB_HOST`, `COUCHDB_USER`, `COUCHDB_PASS`)
- run `pytest --cov=aiocouch`


## Generate documentation

- Install dependencies using `pip install '.[docs]'`
- switch to the `docs` directory: `cd docs`
- run `make html`
