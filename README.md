
# 🔐 VaultDB

![Coverage](https://img.shields.io/badge/coverage-93%25-brightgreen)

**VaultDB** is a zero-config, encrypted document database for Python developers who want built-in security without thinking about cryptography.

- ⚡ Fast local JSON-backed store
- 🔐 AES-256 encryption by default (via Fernet)
- 🧠 Developer-friendly API
- 🧂 Salt-based key derivation with secure passphrase handling
- 🧰 Simple `.insert()`, `.get()`, `.find()` methods
- 📦 Single `.vault` file with embedded metadata and encryption salt

---

## 🚀 Quick Start

```python
from vaultdb import VaultDB

vault = VaultDB.open("notes.vault", "correct horse battery staple")
vault.insert({"_id": "alice", "email": "alice@example.com"})

doc = vault.get("alice")
print(doc["email"])
```

---

## 🔐 VaultDB Guarantees Cryptographic Isolation

VaultDB ensures that **each vault file is isolated by design** — even if the same passphrase is used across different vaults. This is achieved through random salt-based key derivation.

```python
from vaultdb import VaultDB
from vaultdb.errors import CryptoError

# Create two vaults with the same passphrase
vault1 = VaultDB.open("vault1.vault", "hunter2")
vault2 = VaultDB.open("vault2.vault", "hunter2")

# Insert a document into vault1
vault1.insert({"_id": "secret", "msg": "top secret"})

# Manually move the encrypted blob from vault1 into vault2 (for testing)
vault2.store.insert(vault1.store.data["secret"])

# Trying to decrypt it with the wrong vault (vault2) fails:
try:
    vault2.get("secret")
except CryptoError:
    print("Decryption failed — keys are isolated.")
```

This proves:

- ✅ Vaults using the same passphrase **still derive different keys**
- ✅ Vaults **cannot decrypt each other's data**
- ✅ VaultDB is **zero-trust and secure by default**

---

## 📁 File Format

Each `.vault` file stores:

```json
{
  "_meta": {
    "vault_version": "1.0.0",
    "created_at": "...",
    "salt": "base64...",
    "app_name": "..."
  },
  "documents": {
    "abc123": {
      "_id": "abc123",
      "data": "gAAAAABh..."  // Fernet-encrypted blob
    }
  }
}
```

---

## 🔑 Key Export

VaultDB now supports exporting encryption keys and salts securely.

- `VaultDB.export_key()` allows you to export the derived key and salt either as a dictionary or write it to a `.vaultkey` file.
- Use `ExportFormat.DICT` for programmatic access or `ExportFormat.JSON` to export to a file.

### Example:

```python
# Export to dict
export = vault.export_key()
print(export)

# Export to file
file_path = vault.export_key(export_format=ExportFormat.JSON, filepath="mykey")
print(f"Key exported to: {file_path}")
```

**⚠️ WARNING**: It is your responsibility to securely store the exported key and salt. Exposing or losing the key could compromise your encrypted data. Only share with trusted parties and ensure it is handled with the highest security standards. 

If you prefer not to manage the key manually, VaultDB can handle key management for you automatically when using `VaultDB.open()`, so you only need to securely store your passphrase.

---

## 🛠 Roadmap

- [x] Encrypted storage with passphrase
- [x] Transparent key handling with salt
- [x] Query and insert API
- [x] Metadata embedding
- [x] Key export functionality
- [ ] CLI inspector (`vault inspect my.vault`)
- [ ] PyPI package + loom demo

---

## 🪪 License

MIT © 2025 VaultDB Project
