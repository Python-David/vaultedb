# VaultDB `test_encrypted_storage_find.py`: Test Plan for `.find()` Method

## Overview

This file tests VaultDB’s `.find()` method in `EncryptedStorage`. The goal is to ensure encrypted documents can be **queried naturally**, just like in Firebase or Mongo — while staying fully secure.

Timi can now look up documents using simple filters, without worrying about encryption.

---

## ✅ Test Scenarios

### 🔎 `test_find_exact_match`
* Timi saves two entries and wants to find only the one matching `{"name": "Alice"}`.
* VaultDB returns one match with the correct `_id`.

### ❌ `test_find_no_match`
* Timi queries for a non-existent value.
* VaultDB returns an empty list — no false positives.

### 🔁 `test_find_multiple_matches`
* Several entries have the same tag and status.
* `.find()` returns only the entries that match all criteria.

### 🆓 `test_find_with_empty_filter_returns_all`
* An empty dict (`{}`) should return all available decrypted documents.
* This helps with basic listing or dashboard behavior.

### 🚫 `test_find_with_invalid_filter_type_raises`
* Passing a string or number instead of a dict raises `InvalidDocumentError`.
* Ensures consistent API behavior and avoids silent bugs.

### 🎭 `test_find_type_mismatch_does_not_match`
* A string is used to query a numeric field (`{"count": "10"}` vs actual `10`).
* VaultDB returns no match — exact match only.

### 💥 `test_find_skips_corrupt_data`
* A document in the vault is corrupted on disk.
* `find()` triggers `.list(strict=True)`, which raises `CryptoError`.

---

## Philosophy

* All query logic is **performed post-decryption**
* No indexing or partial matches yet — strict key/value exact match
* Built on top of `.list(strict=True)` to reuse secure loading path

---

## Why This Matters

`.find()` makes encrypted storage **usable**. Without it, Timi could store data securely — but she couldn’t **query** it easily. Now she can do both:

🔐 **Security** + 🔎 **Searchability**  
→ That’s real power.

