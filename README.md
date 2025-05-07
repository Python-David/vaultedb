# 🔐 VaultDB

**VaultDB** is a zero-config, Python-native, document database that stores all your data encrypted by default. Built for developers who care about privacy, speed, and simplicity.

---

## ✨ Features

- 📦 JSON-based document storage
- 🔒 Transparent AES-256 encryption (completed!)
- 🧠 Pythonic API: `vault.insert()`, `vault.find()`...
- 💥 Atomic file writes to prevent corruption
- 🔍 Simple querying with `.find()` (no index, linear scan)
- 🧪 100% tested with `pytest`
- 📁 Local-first: no server or config needed

- 📦 JSON-based document storage
- 🔐 End-to-end encryption (coming in Phase 2)
- 🧠 Human-readable API, built with Python in mind
- 🧪 Tested with `pytest`
- 💥 Atomic file writes to prevent corruption
- 📁 Local-first: no server required
- 🔍 Simple querying (planned)
- 🔑 Key management system (planned)

---

## 📦 Installation

Coming soon to PyPI. For now, clone and use locally:

```bash
git clone https://github.com/YOUR_USERNAME/vaultdb.git
cd vaultdb
```

## 🧠 Usage (Phase 1 Complete!)

```python
from vaultdb.encrypted_storage import EncryptedStorage
from vaultdb.crypto import generate_key, generate_salt

# Generate encryption key from passphrase
salt = generate_salt()
key = generate_key("my-passphrase", salt)

# Create encrypted vault
vault = EncryptedStorage("vault.json", key)

# Insert a document
doc_id = vault.insert({"name": "Alice", "email": "alice@example.com"})

# Fetch it back
doc = vault.get(doc_id)

# Update it
vault.update(doc_id, {"role": "admin"})

# Delete it
vault.delete(doc_id)

# Find documents by field
results = vault.find({"name": "Alice"})
```

```python
from vaultdb.storage import DocumentStorage

store = DocumentStorage("vault.json")

# Insert a document
doc_id = store.insert({"name": "Alice"})

# Fetch it back
doc = store.get(doc_id)

# Update it
store.update(doc_id, {"age": 30})

# Delete it
store.delete(doc_id)
```

## 🧪 Running Tests

```bash
pytest
```

## 📂 Project Structure

```
vaultdb/
├── storage.py                  # Plaintext document store
├── encrypted_storage.py        # Encrypted wrapper with Fernet
├── crypto.py                   # AES-based encryption functions
├── errors.py                   # Custom VaultDB error types
├── tests/
│   ├── test_storage.py         # Tests for plaintext store
│   ├── test_encrypted_storage.py # Tests for encrypted storage
│   └── test_crypto.py          # Tests for crypto utils
├── demo/example_usage.py       # End-to-end usage example
├── docs/
│   ├── storage.md              # Component-level doc (plaintext)
│   ├── encrypted_storage_user_doc.md  # Developer guide
│   ├── test_storage.md         # Timi’s user-centered test narrative
│   └── test_encrypted_storage_find.md # Edge-case test walkthrough
├── README.md
├── LICENSE
```

```
vaultdb/
├── storage.py          # Core storage engine
├── test_storage.py     # Unit tests for storage
├── storage.md          # Component-level documentation
├── LICENSE
├── README.md
```

## 🚧 Roadmap (MVP)

| Phase | Goal |
|-------|------|
| 1 🔄 | Core engine: encrypted JSON storage, querying, Pythonic API (final task remaining) |
| 2 🔐 | Developer trust: file metadata, CLI, key handling |
| 3 🧪 | Demos: notebook, PyPI package, data leak test |
| 4 🚀 | Public launch: GitHub, social push, waitlist |

| Phase | Goal |
|-------|------|
| 1 | ✅ Core storage engine (plaintext, atomic, JSON) |
| 2 | 🔐 Transparent encryption, key handling, CLI |
| 3 | 🧪 Notebook/demo, PyPI-ready package |
| 4 | 🚀 Public launch, social push, waitlist |

## 🛡 License

This project is licensed under the MIT License – see LICENSE for details.

## 👋 Contributing

This is a solo build sprint right now, but if you're passionate about privacy, open-source, or Python — feel free to open an issue or get in touch.

## 📣 Stay in the loop

Follow the journey on [LinkedIn](https://www.linkedin.com/in/python-david/) or star this repo to support development.
