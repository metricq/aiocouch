# v1.2.0

- Adds documentation

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
