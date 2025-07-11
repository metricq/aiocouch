# v4.0.1

- CIing is hard :C

# v4.0.0

- Added `revs()` method to `Document` that allows to list all available revs of that document
- Added `conflicts()` method to `Document` that allows to get a list of all conflicts
- Improved error handling for lockout introduced in CouchDB 3.4. See also https://docs.couchdb.org/en/stable/whatsnew/3.4.html#version-3-4-0
- Fix minor issues in tests, coverage and linting
- [BREAKING] Behaviour changing parameters can no longer be passed as args, but must be kwargs 

# v3.0.1

- Fixed lost query params in database create method
- Added Python 3.12 and CouchDB 3.3 to test matrix

# v3.0.0

- Added support for `/db/_purge` endpoint, which allows to remove all references to a document
- Added `Document.json` property, which is a dict representing the document data
- Added `HTTPResponse` as return from certain `Document` endpoints that may give 202 Accepted HTTP status codes
- Improved documentation
- [BREAKING] `Document.clone()` no longer returns the cloned document

# v2.2.2

- Fixed BasicAuth for UTF-8 encoded credentials

# v2.2.1

- Fixed unexpected exception when calling `CouchDB.create(exists_ok=True)` in case of race conditions

# v2.2.0

- Added support for `/db/_changes` endpoint, which allows to listen for change events
- Added support for `/db/_index` endpoint, which allows to create indexes on databases
- Improved documentation

# v2.1.1

- Fixes missing module dependency
- Added Python 3.10 to list of supported python versions
- CI: Running tests in isolated environment from linting

# v2.1.0

- Adds context managers for automatic saving of Documents
- Adds documentation for attachments and bulk operations
- Adds Mypy typing support

# v2.0.1

- Fixes a crash in bulk operations
- Fixes a redundant HEAD request during the creation of design document objects

# v2.0.0

- Adds documentation
- Removes design documents from the `docs()` iteration on Database instances by default [Breaking change]
- Adds `include_ddocs` parameter to `docs()` method to allow the iteration over **all** documents

# v1.1.0

- Adds `Database.create_docs` similar to `update_docs`, but without retrieving documents first
- Renames `Document.fetch_info()` to `info()`
- Adds data argument to Document
- Adds ok and error member to `update_docs` and `create_docs` context managers

# v1.0.1

- Fixes error while handling a ConflictError for newly created documents
- Internal refactoring

# v1.0.0

- Initial release
