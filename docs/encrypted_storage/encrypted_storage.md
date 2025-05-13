# vaultedb: encrypted_storage.py Module Documentation

## Overview

`encrypted_storage.py` wraps the low-level `DocumentStorage` to provide **transparent encryption** and **decryption** of all documents. It ensures that data is encrypted before writing to disk and decrypted only upon retrieval, using a provided key.

This module enforces vaultedb’s zero-trust principle: even the raw file on disk contains no readable data, and developers don't need to manage encryption logic manually.

## Responsibilities

- Encrypt documents before writing to disk
- Decrypt documents only on read
- Ensure `_id` remains plaintext for lookups
- Raise errors for malformed or non-dict documents
- Gracefully handle corrupted data (with strict and non-strict modes)

## Constructor

### `__init__(self, path: str, key: bytes)`
Initializes the encrypted store.

- `path`: Path to the storage file (usually `.vault`)
- `key`: 32-byte encryption key (derived from passphrase + salt)

---

## Methods

### `insert(doc: dict) -> str`
- Validates input is a dict.
- Encrypts the document using Fernet.
- Stores as `{_id: ..., data: <encrypted>}` in `DocumentStorage`.

### `get(doc_id: str) -> Optional[dict]`
- Retrieves and decrypts the document with the given `_id`.

### `update(doc_id: str, updates: dict) -> bool`
- Loads, decrypts, updates, re-encrypts, and stores the document.

### `find(filter: dict) -> List[dict]`
- Decrypts all documents and filters them by the given key-value pairs.
- Only returns documents where all fields in `filter` match exactly.
- Accepts an empty dict (`{}`) to return all documents.
- Input must be a dict — raises `InvalidDocumentError` otherwise.

**Example:**
```python
vault.find({"name": "Alice"})
# → returns all docs where name == "Alice"
```

### `delete(doc_id: str) -> bool`
- Deletes the document by ID from underlying storage.

### `list(strict: bool = True) -> List[dict]`
- Returns all decrypted documents.
- If `strict=False`, skips corrupted or missing data entries.

---

## Error Classes

- `CryptoError`: Raised when encryption/decryption fails.
- `InvalidDocumentError`: Raised when input is not a dict.
- `DuplicateIDError`: Raised on duplicate `_id`.

---

## Notes

- `_id` remains plaintext to enable fast lookup.
- All other document data is encrypted using Fernet (AES-128 in CBC mode).
- Works seamlessly with `generate_key(passphrase, salt)` from `crypto.py`.
