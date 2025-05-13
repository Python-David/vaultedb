# vaultedb: storage.py Module Documentation

## Overview
`storage.py` is the foundational layer of vaultedb's local persistence engine. It handles loading and saving document data to a flat file on disk, using a JSON-based structure. This is the lowest level of interaction with Vault data and serves as the backend for higher-level operations like encryption, querying, and API access.

## Responsibilities
* Store all documents in a single JSON file
* Assign a unique `_id` to each document (UUIDv4 unless provided)
* Ensure atomicity of writes using temp files + `os.replace`
* Load the store from disk gracefully, including empty files
* Prevent accidental data loss by enforcing `_id` uniqueness
* Validate that inserted and updated documents are dictionaries
* Support listing all documents
* Store vault-level metadata like version, creation time, and app name

## Methods

### `__init__(self, path: str, app_name: Optional[str] = None)`
Initializes the document store at the given path. Optionally adds an `app_name` field to the vault metadata.

### `_load(app_name: Optional[str])`
Attempts to load the JSON file from disk. If file is missing, empty, or in legacy format, initializes a new metadata block.

### `_atomic_write()`
Writes the current state to a temporary file and then replaces the target file. Guarantees atomicity of write.

### `insert(doc: dict) -> str`
* Validates that `doc` is a dictionary
* Auto-generates `_id` if not present
* Raises `DuplicateIDError` if `_id` already exists
* Saves the store to disk

### `get(doc_id: str) -> Optional[dict]`
Returns the document with the given `_id`, or `None` if not found.

### `update(doc_id: str, updates: dict) -> bool`
* Validates that `updates` is a dictionary
* Updates the existing document with `updates`
* Returns `True` if successful, `False` if `_id` not found

### `delete(doc_id: str) -> bool`
Removes the document with the given `_id` if it exists. Returns `True` if deleted.

### `list() -> List[dict]`
Returns all stored documents as a list.

## File Format
vaultedb files now use the following schema:

```
{
  "_meta": {
    "vault_version": "1.0.0",
    "created_at": "2025-05-07T14:01:00Z",
    "app_name": "TimiJournal"
  },
  "documents": {
    "a1b2c3": {"_id": "a1b2c3", "name": "Alice"},
    "d4e5f6": {"_id": "d4e5f6", "name": "Bob"}
  }
}
```

This structure supports metadata introspection and future versioning while keeping all documents inside the `documents` field.

## Error Classes
* `StorageError`: Raised when loading or saving to disk fails
* `InvalidDocumentError`: Raised when a document is not a dict
* `DuplicateIDError`: Raised when inserting a document with an existing `_id`

## Tests
* `test_insert_and_get`
* `test_update_and_get`
* `test_delete`
* `test_list_documents`
* `test_duplicate_id_insert_raises`
* `test_insert_does_not_overwrite_existing_doc`
* `test_json_file_format_after_insert`
* `test_atomic_write_failure_does_not_corrupt_file`
* `test_metadata_written`
* `test_legacy_file_format_loads_correctly`

## Notes
* This module is designed to be encryption-agnostic. All encryption logic is layered on top.
* The `_meta` block is automatically generated and updated internally.
* Older vault files (pre-metadata) are still supported.
* This documentation will evolve further as we add sync features and vault inspection tools in Phase 2.