# 🔐 VaultDB

![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen)

> **SQLite for encrypted documents.**  
> All the simplicity of SQLite — but your data is always encrypted, always private.


**VaultDB** is a zero-config, encrypted document database for Python developers who want built-in security without dealing with cryptography directly.

- ⚡ Fast local JSON-backed store
- 🔐 AES-256 encryption using Fernet
- 🧠 Pythonic `.insert()`, `.get()`, `.find()` API
- 🧂 Salt-based key derivation per vault
- 🔍 Inspectable, portable `.vault` file format
- 🧰 Optional CLI tool for safe metadata inspection: trust without decrypting
- 📦 Single-file storage with embedded metadata and salt

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

## ⭐ VaultDB Design Principles

### 🔐 Zero-Config Encryption

VaultDB encrypts every document automatically using AES-256 (via Fernet). Developers only provide a passphrase — VaultDB handles the rest.

- No need to manage keys manually
- All data is encrypted at rest
- Only `_id` is stored unencrypted for lookup

---

### 🧂 Salt-Based Key Derivation

Each vault file embeds a **unique salt**, which is used with your passphrase to derive the encryption key using PBKDF2.

- Even with the same passphrase, each vault produces a different key
- Defends against rainbow table and credential reuse attacks
- Salt is safely stored in `_meta["salt"]`

---

### ✅ Cryptographic Isolation Guarantee

Even if two vaults are opened with the **same passphrase**, they **cannot decrypt each other's documents**.

```python
from vaultdb import VaultDB
from vaultdb.errors import CryptoError

vault1 = VaultDB.open("vault1.vault", "hunter2")
vault2 = VaultDB.open("vault2.vault", "hunter2")

vault1.insert({"_id": "secret", "msg": "top secret"})

# Manually copy raw encrypted doc into vault2
vault2.store.insert(vault1.store.data["secret"])

try:
    vault2.get("secret")
except CryptoError:
    print("Decryption failed — vaults are isolated.")
```

✅ Proves cryptographic boundaries are enforced even with identical passphrases.

---

### 📁 File Format: Inspectable and Portable

Each `.vault` file is a valid JSON document containing:

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
      "data": "gAAAAABh..."  // Encrypted blob
    }
  }
}
```

- JSON-readable
- Safe to commit or sync
- Portable across systems

---

## 🔍 CLI Inspector: Trust Without Decryption

Use the built-in CLI to inspect metadata and document IDs — **without decrypting any content**.

```bash
vault inspect notes.vault
```

Or:

```bash
python -m vaultdb.cli inspect notes.vault
```

### Output Example

```
VaultDB Inspector 🔍
------------------------------
📁 File: notes.vault
📅 Created At: 2025-05-08T12:00:00Z
🔖 Vault Version: 1.0.0
🏷️ App Name: MyJournal
🧂 Salt: wvN2t4c89Ne8... (truncated)
📄 Document Count: 2
🆔 IDs (first 2):
  - alice
  - bob
```

### CLI Options

| Flag           | Description                                      |
|----------------|--------------------------------------------------|
| `--json`       | Output metadata as JSON                          |
| `--quiet`      | Suppress headers and emojis                      |
| `--max-ids N`  | Show N IDs instead of default 10                 |

---

## ⚡ Performance and Scalability Notes

VaultDB loads the entire vault into memory and writes atomically. This favors **simplicity and safety**.

### Practical Limits

| Factor              | Safe Range            | Notes                              |
|---------------------|-----------------------|-------------------------------------|
| Document count      | Up to ~10,000–25,000  | Full scans, no indexing             |
| Vault file size     | Up to ~100MB          | Depends on doc size                |
| Query performance   | Linear (`.find()`)    | Fast for small–medium vaults       |
| Storage format      | Flat JSON             | Reliable and portable              |

VaultDB is not meant to replace traditional databases — it’s built for privacy-first applications, AI agents, regulated industries, and sensitive local workflows where data ownership and encryption must come first.

It shines in use cases like:

📝 Encrypted journaling and local note-taking

🤖 AI agents that store sensitive context or user profiles on-device

🩺 Health and therapy apps needing offline, encrypted session data

📦 Configuration snapshots that shouldn’t ever hit the cloud

🔐 Secure local logging for audit trails or confidential workflows

VaultDB is ideal when:

1. You want to ensure data at rest is always encrypted

2. You need verifiability and trust, not complexity

3. You want to keep control without building custom crypto

Built for builders who take privacy seriously — even when no one's watching.

---

## 🧪 Full Test Coverage

- 94%+ test coverage via `pytest` + `coverage`
- Unit tests cover: storage, encryption, passphrase handling, CLI, key export
- CLI tested via subprocess with real `.vault` files

---

## 📦 Installation

Install with Poetry:

```bash
poetry install
```

Install from PyPI (when published):

```bash
pip install vaultdb
```

Run the CLI:

```bash
vault inspect your.vault
```

---

## 🛠 Roadmap

- [x] Encrypted storage with passphrase
- [x] Transparent key handling with salt
- [x] Query and insert API
- [x] CLI inspector tool
- [x] PyPI-ready packaging
- [ ] Exportable vault migration utility
- [ ] Indexing or streaming modes (future optional)

---

## 🪪 License

MIT © 2025 VaultDB Project
