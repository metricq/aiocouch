# aiocouch
An asynchronous client library for CouchDB 2.0 based on asyncio using aiohttp

It provides a transparent caching for database and document objects synchronized
within the same runtime environment automatically. Users have to be aware of concurrent
modifications by other clients.

## Installation

Run `pip install .` within the root directory.

## Run tests

- Setup the CouchDB URL and credentials using the environment variables
- (Optional) install using `pip install --editable '.[tests]'`
- run pytest --cov=aiocouch


Or shorter for CI:

```
COUCHDB_HOST=localhost:5984 COUCHDB_USER=admin COUCHDB_PASS=admin python setup.py test
```
