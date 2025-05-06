import os
import json
import sys
import uuid
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vaultdb.encrypted_storage import EncryptedStorage
from vaultdb.crypto import generate_key, generate_salt, CryptoError
from vaultdb.errors import InvalidDocumentError, DuplicateIDError

@pytest.fixture
def encrypted_store():
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        path = tf.name
    salt = generate_salt()
    key = generate_key("test-passphrase", salt)
    store = EncryptedStorage(path, key)
    yield store
    os.remove(path)

def test_insert_and_get(encrypted_store):
    doc_id = encrypted_store.insert({"name": "Alice"})
    doc = encrypted_store.get(doc_id)
    assert doc["_id"] == doc_id
    assert doc["name"] == "Alice"

def test_insert_invalid_type(encrypted_store):
    with pytest.raises(InvalidDocumentError):
        encrypted_store.insert(["not-a-dict"])

def test_insert_duplicate_id(encrypted_store):
    doc = {"_id": "fixed-id", "name": "Original"}
    encrypted_store.insert(doc)
    with pytest.raises(DuplicateIDError):
        encrypted_store.insert({"_id": "fixed-id", "name": "Duped"})

def test_update_success(encrypted_store):
    doc_id = encrypted_store.insert({"name": "Bob"})
    success = encrypted_store.update(doc_id, {"email": "bob@example.com"})
    assert success
    doc = encrypted_store.get(doc_id)
    assert doc["email"] == "bob@example.com"

def test_update_invalid_type(encrypted_store):
    doc_id = encrypted_store.insert({"name": "Charlie"})
    with pytest.raises(InvalidDocumentError):
        encrypted_store.update(doc_id, "not-a-dict")

def test_update_nonexistent(encrypted_store):
    result = encrypted_store.update("does-not-exist", {"name": "X"})
    assert result is False

def test_delete_success(encrypted_store):
    doc_id = encrypted_store.insert({"name": "DeleteMe"})
    deleted = encrypted_store.delete(doc_id)
    assert deleted
    assert encrypted_store.get(doc_id) is None

def test_delete_nonexistent(encrypted_store):
    assert encrypted_store.delete("nope") is False

def test_list_documents(encrypted_store):
    encrypted_store.insert({"name": "Doc1"})
    encrypted_store.insert({"name": "Doc2"})
    docs = encrypted_store.list()
    names = [doc["name"] for doc in docs]
    assert "Doc1" in names
    assert "Doc2" in names
    assert len(docs) == 2

def test_corrupt_data_strict_mode(encrypted_store):
    doc_id = encrypted_store.insert({"name": "Eve"})
    with open(encrypted_store.store.path, "r+", encoding="utf-8") as f:
        raw = json.load(f)
        raw[doc_id]["data"] = "!@#$%^&*()"  # guaranteed invalid
        f.seek(0)
        json.dump(raw, f)
        f.truncate()
    with pytest.raises(CryptoError):
        encrypted_store.list(strict=True)

def test_corrupt_data_non_strict_mode(encrypted_store):
    doc_id = encrypted_store.insert({"name": "Frank"})
    with open(encrypted_store.store.path, "r+", encoding="utf-8") as f:
        raw = json.load(f)
        raw[doc_id]["data"] = "!@#$%^&*()"  # guaranteed invalid
        f.seek(0)
        json.dump(raw, f)
        f.truncate()
    docs = encrypted_store.list(strict=False)
    assert isinstance(docs, list)
    assert len(docs) == 0  # corrupted doc is skipped
