# 🔐 VaulteDB

![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen)

> **SQLite for encrypted documents.**  
> All the simplicity of SQLite — but your data is always encrypted, always private.

**VaulteDB** is a zero-config, encrypted document database for Python developers who want built-in security without dealing with cryptography directly.

- ⚡ Fast local JSON-backed store
- 🔐 AES-256 encryption using Fernet
- 🧠 Pythonic `.insert()`, `.get()`, `.find()` API
- 🧂 Salt-based key derivation per vault
- 🔍 Inspectable, portable `.vault` file format
- 🧰 Optional CLI tool for safe metadata inspection
- 📆 Append-only encrypted audit log (optional)
- 🗃️ Single-file storage with embedded metadata and salt

---

## 🚀 Quick Start

```python
from vaultedb import vaultedb

vault = vaultedb.open("notes.vault", "correct horse battery staple")
vault.insert({"_id": "alice", "email": "alice@example.com"})

print(vault.get("alice")['email'])
```

---

## ✨ Why VaulteDB?

- ❌ SQLCipher: low-level SQL only
- 🔐 MongoDB: enterprise-only FLE, complex setup
- ⚡ Evervault: hosted service, not a library
- 🚀 vaultedb: open-source, local, encrypted, and simple

---

## ⭐ Design Principles

### 🔐 Zero-Config Encryption
VaulteDB encrypts every document automatically. Developers only provide a passphrase. vaultedb handles:
- Key derivation (PBKDF2)
- AES-256 encryption (via Fernet)
- Embedded salts

### 🧂 Salt-Based Key Derivation
Each vault embeds a **unique salt**. Even with the same passphrase, every vault is isolated.

```json
"salt": "base64-encoded-value"
```

### ✅ Vault Isolation Guarantee
Same passphrase ≠ same key. Copying blobs across vaults doesn't work:

```python
vault1 = vaultedb.open("vault1.vault", "hunter2")
vault2 = vaultedb.open("vault2.vault", "hunter2")

vault1.insert({"_id": "secret", "msg": "top secret"})
vault2.store.insert(vault1.store.data["secret"])

from vaultedb.errors import CryptoError
try:
    vault2.get("secret")
except CryptoError:
    print("✅ Vaults are isolated by salt")
```

### 📅 Portable File Format
Each `.vault` file is valid JSON:
```json
{
  "_meta": {
    "vault_version": "1.0.0",
    "created_at": "...",
    "salt": "...",
    "app_name": "..."
  },
  "documents": {
    "abc123": {"_id": "abc123", "data": "gAAAAB..."}
  }
}
```

---

## 🔍 CLI Inspector: Trust Without Decryption
```bash
vault inspect notes.vault
```
```bash
python -m vaultedb.cli inspect notes.vault --json --quiet
```
See vault metadata, salt, and IDs without ever decrypting.

---

## 🗓️ Logging: Encrypted Audit Trails (Optional)
Enable audit logging:
```python
vault = vaultedb.open("secure.vault", "hunter2", enable_logging=True)
vault.insert({"_id": "day1", "note": "Encrypted entry"})
```

All actions are encrypted and logged to `.vaultlog`:
```json
{
  "op": "insert",
  "_id": "day1",
  "at": "2025-05-13T11:00:00Z",
  "meta": {}
}
```
- ✉️ Export logs with `vault.get_audit_log().export_json("out.json")`
- 🚨 Detect tampering: logs can't be forged or decrypted without key

---

## ⬆ MVP Status: Complete
This project is currently an MVP focused on local security and DX:
- ✅ Local document storage
- ✅ Transparent encryption
- ✅ Key export
- ✅ CLI inspector
- ✅ Optional audit logging

Planned post-MVP:
- [ ] Indexing and query optimization
- [ ] Vault sync over S3 or filesystem
- [ ] Multi-user vault support

---

## 🔗 Use Cases
- 📋 Local note-taking with privacy
- 🧑‍💻 AI agents storing context
- 💼 Secure local logging in compliance environments
- 🚗 Field apps storing offline snapshots securely

---

## 📊 Test Coverage
- 94%+ tested
- Core coverage: encryption, storage, logging, passphrase
- CLI tested via subprocess

---

## 📦 Installation
```bash
pip install vaultedb  # or use poetry install if cloning locally
```

---

## 🎥 Demo & Examples
- [`example_usage.py`](demo/example_usage.py) — CLI-based demo
- [`demo_notebook.ipynb`](demo/demo_notebook.ipynb) — Interactive walkthrough

---

## 🌟 Support vaultedb
- ⭐ Star us on GitHub: [vaultedb](https://github.com/yourusername/vaultedb)
- 📢 Share your feedback
- 📱 Try the demo or install from PyPI

Built for developers who take privacy seriously.

---

## 🚩 License
MIT © 2025 VaulteDB Project
