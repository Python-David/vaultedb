# vaultedb `storage.py`: User-Centered Documentation

## Overview

`storage.py` is the foundation of vaultedb's local document storage engine. It provides a lightweight, developer-friendly way to store, retrieve, and manage JSON documents on disk. This module ensures each document has a unique `_id`, supports atomic file writes to prevent corruption, and lays the groundwork for later encrypted storage layers.

This documentation walks through the module from the perspective of a real user: **Timi**, a developer building a journaling app who wants a private, zero-setup, local database.

## User Story: Meet Timi

Timi is building a local journaling app. She wants to save daily entries safely on disk without setting up PostgreSQL or MongoDB. She chooses vaultedb for its simplicity, atomic safety, and built-in encryption.

## Step-by-Step: How `storage.py` Helps Timi

### 1. Initialization

```python
store = DocumentStorage("journal.json")
```

* vaultedb creates or loads the file `journal.json`.
* If it doesn't exist yet, vaultedb starts fresh with an empty store.
* If it exists, vaultedb loads its content into memory.

**Safety:** If the file is empty or corrupted, vaultedb fails gracefully with a helpful error.

### 2. Inserting Documents

```python
store.insert({"title": "My First Day", "mood": "🌞"})
```

* vaultedb checks that the document is a Python dictionary.
* It assigns a UUID `_id` if one isn't provided.
* If the `_id` already exists, vaultedb raises a `DuplicateIDError`.
* It writes the entire updated store to disk **atomically** (via a temp file and `os.replace`).

**Why This Matters:** Timi doesn't have to worry about ID generation, data corruption, or managing database setup.

### 3. Reading Documents

```python
store.get("a1b2c3d4")
```

* Returns the document with that `_id`, or `None` if not found.

**Perfect for:** displaying journal entries, search, linking.

### 4. Updating Documents

```python
store.update("a1b2c3d4", {"tags": ["gratitude"]})
```

* vaultedb merges the update dict with the existing document.
* Writes the change atomically to disk.
* Returns `True` if successful, `False` if `_id` doesn't exist.

**Why This Matters:** Easy to add metadata, update mistakes, or fix typos.

### 5. Deleting Documents

```python
store.delete("a1b2c3d4")
```

* Deletes the document if found.
* Saves the updated store safely.
* Returns `True` or `False` depending on existence.

**Use Case:** Timi deletes an embarrassing rant or removes test data.

### 6. Listing All Entries

```python
store.list()
```

* Returns a list of all documents currently in memory.

**Use Case:** Populate UIs, back up entries, export data.

## Behind the Scenes: Design Highlights

### 🔐 Atomic Safety
* All writes go through a temporary file before replacing the original.
* Prevents data loss during crashes.

### ✅ Input Validation
* Only dictionaries are allowed for documents and updates.
* Duplicate `_id`s are caught early.

### ⚠️ Errors Made Clear
* Uses `InvalidDocumentError`, `DuplicateIDError`, and `StorageError` so developers know what went wrong and how to fix it.

### ⚙️ Simple JSON Format

```json
{
  "a1b2c3": {"_id": "a1b2c3", "title": "Day 1", "mood": "🌞"},
  "d4e5f6": {"_id": "d4e5f6", "title": "Day 2", "mood": "😔"}
}
```

* Easy to inspect, back up, and debug.

## Summary

vaultedb's `storage.py` makes it effortless for developers like Timi to build apps with local persistence, safely and intuitively.

It provides everything you'd expect from a tiny database — inserts, updates, deletes, atomic safety — but keeps things minimal and familiar.

This is the foundation for all encryption, querying, and developer experience that vaultedb builds on.