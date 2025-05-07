# VaultDB `test_storage.py`: User-Centered Test Documentation

## Overview

This file contains automated tests that ensure `storage.py` — VaultDB's core local document store — behaves exactly as promised. These tests are written from the perspective of **Timi**, a journaling app developer who depends on VaultDB for privacy, simplicity, and peace of mind.

Each test represents a real action Timi might take — or a mistake she might make — and checks that VaultDB handles it gracefully and safely.

## 🧪 Test Scenarios — Through Timi's Eyes

### ✅ `test_insert_and_get`
"I want to save a journal entry and retrieve it later."
* Proves that `insert()` assigns an `_id` and stores the document.
* Confirms `get()` returns the exact entry by `_id`.

### ❌ `test_insert_invalid_type`
"Oops, I passed a list instead of a dictionary."
* Ensures VaultDB rejects invalid types with a clear error (`InvalidDocumentError`).

### ✏️ `test_update_and_get`
"I want to add a tag to an old entry."
* Checks that `update()` merges fields and persists the change.

### ❌ `test_update_invalid_type`
"I mistakenly passed a string instead of a dict when updating."
* VaultDB raises `InvalidDocumentError`, preventing corruption.

### 🗑️ `test_delete`
"I want to delete an embarrassing entry forever."
* Confirms the entry is removed from both memory and disk.

### 📋 `test_list_documents`
"I want to show all journal entries in my app."
* Validates that `list()` returns every saved document.

### 💥 `test_load_invalid_json_raises`
"I manually edited the file and broke it."
* VaultDB detects broken JSON and raises `StorageError` — fails gracefully.

### 🆔 `test_duplicate_id_insert_raises`
"I reused an ID by mistake."
* VaultDB blocks the insert and raises `DuplicateIDError` to protect data integrity.

### 📂 `test_json_file_format_after_insert`
"What does VaultDB actually write into `journal.json`?"
* Confirms the format is a JSON object of `{_id: document}` pairs.

### 💾 `test_atomic_write_failure_does_not_corrupt_file`
"What if my laptop dies mid-save?"
* Simulates a crash. VaultDB leaves the previous data intact — no corruption.

### ⛔ `test_insert_does_not_overwrite_existing_doc`
"What if I accidentally insert the same ID again?"
* VaultDB protects the original and raises an error instead of overwriting.

### 🔒 `test_large_document_insert`
Placeholder for Phase 2 encryption test — skipped for now.

## Final Thoughts for Developers

Timi's peace of mind comes from knowing that VaultDB:
* Never loses her data
* Fails clearly and safely
* Behaves exactly as expected in real-world situations

These tests are not just correctness checks — they're guarantees.

If you're building on VaultDB, you can trust that these behaviors are locked in and verified.

✅ This is the second user-centered document in VaultDB's developer handbook, joining the main storage engine walkthrough.