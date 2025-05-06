# 🔐 VaultDB

**VaultDB** is a zero-config, Python-native, document database that stores all your data encrypted by default. Built for developers who care about privacy, speed, and simplicity.

---

## ✨ Features

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

## 🧠 Usage (Phase 1)

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
├── storage.py          # Core storage engine
├── test_storage.py     # Unit tests for storage
├── storage.md          # Component-level documentation
├── LICENSE
├── README.md
```

## 🚧 Roadmap (MVP)

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

Follow the journey on LinkedIn or star this repo to support development.
