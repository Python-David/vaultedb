import sys

import pytest
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vaultdb.encrypted_storage import EncryptedStorage
from vaultdb.crypto import generate_key, generate_salt
from vaultdb.errors import InvalidDocumentError, CryptoError
import tempfile

@pytest.fixture
def vault():
    with tempfile.NamedTemporaryFile(suffix=".vault", delete=False) as tf:
        path = tf.name
    salt = generate_salt()
    key = generate_key("find-test-passphrase", salt)
    store = EncryptedStorage(path, key)
    yield store
    os.remove(path)

def test_find_exact_match(vault):
    doc1 = {"name": "Alice", "age": 30}
    doc2 = {"name": "Bob", "age": 40}
    id1 = vault.insert(doc1)
    id2 = vault.insert(doc2)

    results = vault.find({"name": "Alice"})
    assert len(results) == 1
    assert results[0]["_id"] == id1
    assert results[0]["name"] == "Alice"

def test_find_no_match(vault):
    vault.insert({"name": "Charlie", "city": "Lagos"})
    results = vault.find({"name": "Nonexistent"})
    assert results == []

def test_find_multiple_matches(vault):
    vault.insert({"tag": "entry", "status": "draft"})
    vault.insert({"tag": "entry", "status": "draft"})
    vault.insert({"tag": "entry", "status": "published"})
    results = vault.find({"tag": "entry", "status": "draft"})
    assert len(results) == 2

def test_find_with_empty_filter_returns_all(vault):
    vault.insert({"note": "day1"})
    vault.insert({"note": "day2"})
    all_docs = vault.find({})
    assert len(all_docs) == 2

def test_find_with_invalid_filter_type_raises(vault):
    with pytest.raises(InvalidDocumentError):
        vault.find("not-a-dict")

def test_find_type_mismatch_does_not_match(vault):
    vault.insert({"count": 10})
    results = vault.find({"count": "10"})  # string vs int
    assert results == []

def test_find_skips_corrupt_data(vault):
    doc_id = vault.insert({"name": "ValidDoc"})

    # Corrupt the encrypted blob directly
    with open(vault.store.path, "r+", encoding="utf-8") as f:
        import json
        raw = json.load(f)
        raw["documents"][doc_id]["data"] = "!@#$%^&*()"
        f.seek(0)
        json.dump(raw, f)
        f.truncate()

    with pytest.raises(CryptoError):
        vault.find({"name": "ValidDoc"})  # uses strict=True
