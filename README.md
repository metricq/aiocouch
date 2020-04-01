[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
![Python package](https://github.com/metricq/aiocouch/workflows/Python%20package/badge.svg)
[![PyPI version](https://badge.fury.io/py/aiocouch.svg)](https://badge.fury.io/py/aiocouch)

# aiocouch
An asynchronous client library for CouchDB 2.0 based on asyncio using aiohttp

## Installation

Run `pip install .` within the root directory.

## Run tests

- Setup the CouchDB URL and credentials using the environment variables
- (Optional) install using `pip install --editable '.[tests]'`
- run `pytest --cov=aiocouch`


Or shorter for CI:

```
COUCHDB_HOST=http://localhost:5984 COUCHDB_USER=admin COUCHDB_PASS=admin python setup.py test
```
