# v2.2.0

- Added support for /db/_changes endpoint, which allows to listen for change events
- Added support for /db/_index endpoint, which allows to create indexes on databases
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

- Adds Database.create_docs similar to update_docs, but without retrieving documents first
- Renames Document.fetch_info() to info()
- Adds data argument to Document
- Adds ok and error member to update_docs and create_docs context managers

# v1.0.1

- Fixes error while handling a ConflictError for newly created documents
- Internal refactoring

# v1.0.0

- Initial release
