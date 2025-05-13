# vaultedb `test_encrypted_storage.py`: User-Centered Test Documentation

## Overview

This file contains automated tests that ensure `encrypted_storage.py` — vaultedb's transparent encryption wrapper — behaves securely and reliably under real-world usage. These tests are written through the eyes of **Timi**, who now trusts vaultedb not just with her app’s data, but with her users’ privacy.

Each test reflects how encryption should feel: invisible, dependable, and impossible to get wrong accidentally.

---

## 🧪 Test Scenarios — Through Timi's Eyes

### ✅ `test_insert_and_get`
"I want to save an encrypted journal entry and read it back."
* Ensures encryption doesn't interfere with insert or retrieval.
* Verifies `_id` is maintained and the document is returned exactly.

### ❌ `test_insert_invalid_type`
"I accidentally passed something that isn’t a dict."
* vaultedb refuses to encrypt non-dict inputs. Clear `InvalidDocumentError`.

### ❗ `test_insert_duplicate_id`
"I reused the same `_id` — accidentally or maliciously."
* vaultedb blocks overwrites with a `DuplicateIDError`. Original stays safe.

### ✏️ `test_update_success`
"I want to add a tag to a private entry."
* Decrypts, updates, and re-encrypts seamlessly.
* Ensures `update()` behaves securely, with no plaintext leakage.

### ❌ `test_update_invalid_type`
"I mistakenly passed a string when updating."
* vaultedb protects integrity by raising `InvalidDocumentError`.

### ⛔ `test_update_nonexistent`
"I tried updating an ID that doesn’t exist."
* Returns `False` to signal it couldn’t find the doc.

### 🗑️ `test_delete_success`
"I want to delete an encrypted entry forever."
* Confirms it disappears — and won’t decrypt again.

### 🚫 `test_delete_nonexistent`
"Trying to delete something that’s not there."
* vaultedb handles it gracefully — no crash, just `False`.

### 📋 `test_list_documents`
"I want to read and decrypt all entries."
* Tests full round-trip: encrypt → decrypt → confirm fields.
* Validates bulk access without breaking the trust model.

### 💥 `test_corrupt_data_strict_mode`
"What if something (or someone) messes with the vault file?"
* Simulates a broken encrypted blob.
* vaultedb raises a `CryptoError`, warning Timi clearly and safely.

### 🧯 `test_corrupt_data_non_strict_mode`
"I'm running a best-effort recovery after data loss."
* vaultedb skips unreadable entries and loads the rest.
* Critical for disaster recovery or breach handling.

---

## Final Thoughts for Developers

These tests lock in the core promise of vaultedb:

* Your documents are encrypted transparently.
* Errors are handled with clarity and care.
* There’s no “oops” moment that leads to data loss or leaked plaintext.

If you’re building encrypted apps like Timi, these guarantees are not just tests — they’re the armor vaultedb wears for your users.

✅ This is the third user-facing doc in vaultedb’s secure-by-default system — and proof that simplicity and privacy can co-exist.

