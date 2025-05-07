# VaultDB `encrypted_storage.py`: User-Centered Documentation

## Overview

`encrypted_storage.py` is where VaultDB becomes magic. It wraps the low-level `storage.py` system with **transparent encryption**, ensuring that every document Timi saves is fully encrypted on disk — even if someone steals the file, they won’t read a thing.

It’s the same simple Python API she’s already using — but now, her data is secure by default.

## Meet Timi, Again

Timi’s journaling app is taking off. She wants her users' entries to be **private**, **trustworthy**, and **zero-config**. That’s where `EncryptedStorage` comes in. With just a passphrase and one import, she gets real encryption with no extra effort.

```python
from vaultdb.encrypted_storage import EncryptedStorage
from vaultdb.crypto import generate_key, generate_salt

salt = generate_salt()
key = generate_key("my-secret-pass", salt)

vault = EncryptedStorage("journal.vault", key)
```

Done. Now Timi’s data is encrypted before it even hits disk.

---

## What Timi Can Do with `EncryptedStorage`

### 🔐 1. Inserting a Document

```python
vault.insert({"title": "A Private Entry", "mood": "😌"})
```

* Just like before — Timi inserts a dict.
* VaultDB generates a UUID `_id`.
* But under the hood, the full document is encrypted using Fernet (AES-based).
* Only `_id` is stored in plaintext so it can be looked up.

### 🕵️ 2. Reading a Document

```python
vault.get("abc123")
```

* Looks up the `_id`, decrypts the blob, and gives Timi back her original dictionary.

**Fails Gracefully:** If the doc doesn't exist or the data is corrupt, VaultDB returns `None` or raises a helpful `CryptoError`.

### ✏️ 3. Updating a Document
### 🔍 4. Finding Documents

```python
vault.find({"name": "Alice"})
```

* Returns a list of all documents where all fields in the filter match exactly.
* If Timi passes an empty dict (`{}`), VaultDB returns **all decrypted documents**.
* If the filter is not a dictionary, VaultDB raises a `InvalidDocumentError`.

**Examples:**
```python
vault.find({"mood": "happy"})
vault.find({})  # returns all documents
vault.find("not-a-dict")  # ❌ raises InvalidDocumentError
```



```python
vault.update("abc123", {"tags": ["reflection"]})
```

* Retrieves and decrypts the document.
* Merges the update fields.
* Re-encrypts and saves it back.

**No plaintext ever hits disk.**

### 🗑️ 4. Deleting a Document

```python
vault.delete("abc123")
```

* Same behavior as before, just removes the encrypted blob by `_id`.

### 📋 5. Listing All Documents

```python
vault.list()
```

* Decrypts every document in the vault and returns them as a list.
* **Strict mode:** Fails on any corrupted or malformed doc.
* **Loose mode:** Skips over broken entries.

```python
vault.list(strict=False)  # best effort
```

---

## Behind the Curtain: What Makes This Special

### 💡 Transparent Encryption

* Timi doesn’t need to know about AES, keys, or salts.
* VaultDB handles encryption/decryption automatically, internally.

### 🆔 Lookup by Plaintext `_id`

* Only the `_id` is stored unencrypted to allow document access.
* This avoids full scans when fetching or updating one entry.

### ⚠️ Crypto Errors Made Safe

* VaultDB will raise `CryptoError` if something goes wrong — not `KeyError`, not `ValueError`.
* Timi can build reliable error handling around it.

### 🧪 Encrypted On-Disk Format

What’s on disk?

```json
{
  "abc123": {
    "_id": "abc123",
    "data": "gAAAAABk..."
  }
}
```

* `data` is a long encrypted blob.
* Timi can run `cat journal.vault` and see gibberish. That’s the point.

---

## Example: What if the File is Tampered?

```python
# Let's say someone edits the file manually and breaks the blob.
with open("journal.vault", "r+") as f:
    corrupted = json.load(f)
    corrupted["abc123"]["data"] = "not-base64"
    f.seek(0)
    json.dump(corrupted, f)
    f.truncate()

vault.get("abc123")  # 💥 Raises CryptoError
```

VaultDB protects Timi by refusing to decrypt unsafe or invalid data.

---

## Summary

VaultDB’s `encrypted_storage.py` lets Timi:

✅ Store sensitive documents  
✅ Trust that they’re secure — always  
✅ Never touch raw cryptography  

It’s as easy as `.insert()` and `.get()` — but the privacy is military-grade.

Timi sleeps better now.  
Her users trust her app.  
And her disk is full of secrets no one else can read.
