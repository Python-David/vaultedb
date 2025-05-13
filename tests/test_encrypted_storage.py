import os
import json
import sys
import tempfile
import warnings

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vaultedb.encrypted_storage import EncryptedStorage
from vaultedb.crypto import generate_key, generate_salt, CryptoError
from vaultedb.errors import InvalidDocumentError, DuplicateIDError

@pytest.fixture
def encrypted_store():
    with tempfile.NamedTemporaryFile(suffix=".vault", delete=False) as tf:
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
        raw["documents"][doc_id]["data"] = "!@#$%^&*()"  # guaranteed invalid
        f.seek(0)
        json.dump(raw, f)
        f.truncate()
    with pytest.raises(CryptoError):
        encrypted_store.list(strict=True)

def test_corrupt_data_non_strict_mode(encrypted_store):
    doc_id = encrypted_store.insert({"name": "Frank"})
    with open(encrypted_store.store.path, "r+", encoding="utf-8") as f:
        raw = json.load(f)
        raw["documents"][doc_id]["data"] = "!@#$%^&*()"  # guaranteed invalid
        f.seek(0)
        json.dump(raw, f)
        f.truncate()
    docs = encrypted_store.list(strict=False)
    assert isinstance(docs, list)
    assert len(docs) == 0  # corrupted doc is skipped

def test_warns_if_non_vault_extension():
    salt = generate_salt()
    key = generate_key("warn-test", salt)

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
        non_vault_path = tf.name

    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            _ = EncryptedStorage(non_vault_path, key)

            assert any(
                issubclass(warning.category, UserWarning) and
                "recommended to use a `.vault` extension" in str(warning.message)
                for warning in w
            )
    finally:
        os.remove(non_vault_path)

def test_does_not_warn_with_vault_extension():
    salt = generate_salt()
    key = generate_key("safe-test", salt)

    with tempfile.NamedTemporaryFile(suffix=".vault", delete=False) as tf:
        vault_path = tf.name

    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            _ = EncryptedStorage(vault_path, key)

            assert not any(
                issubclass(warning.category, UserWarning) and
                ".vault extension" in str(warning.message)
                for warning in w
            )
    finally:
        os.remove(vault_path)

def test_handles_large_vault_file(encrypted_store):
    # Insert many documents
    for i in range(1000):
        encrypted_store.insert({"index": i, "msg": f"doc-{i}"})

    # Confirm we can list them all
    docs = encrypted_store.list()
    assert len(docs) == 1000

    # Confirm find still works on a late insert
    result = encrypted_store.find({"index": 999})
    assert len(result) == 1
    assert result[0]["msg"] == "doc-999"

