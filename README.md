[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
![Python package](https://github.com/metricq/aiocouch/workflows/Python%20package/badge.svg)
[![PyPI version](https://badge.fury.io/py/aiocouch.svg)](https://badge.fury.io/py/aiocouch)

# aiocouch
An asynchronous client library for CouchDB 2.0 based on asyncio using aiohttp

## Key features

- All requests are asynchronus using aiohttp
- Supports CouchDB 2.x and 3.x
- Support for modern Python ≥ 3.6


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

## Run examples

- Setup the CouchDB URL and credentials using the environment variables
- Install using `pip install --editable '.[examples]'`
- run `python examples/getting_started.py`


## Run tests

- Setup the CouchDB URL and credentials using the environment variables
- (Optional) install using `pip install --editable '.[tests]'`
- run `pytest --cov=aiocouch`


Or shorter for CI:

```
COUCHDB_HOST=http://localhost:5984 COUCHDB_USER=admin COUCHDB_PASS=admin python setup.py test
```

## Generate documentation

- (Optional) install using `pip install --editable '.[docs]'`
- switch to the `docs` directory: `cd docs`
- run `make html`
