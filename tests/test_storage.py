import json
import tempfile
import os
import pytest
import sys
from unittest.mock import patch


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vaultdb.storage import DocumentStorage, StorageError
from vaultdb.errors import InvalidDocumentError, DuplicateIDError


@pytest.fixture
def temp_storage_path():
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        yield tf.name
    os.remove(tf.name)

def test_insert_and_get(temp_storage_path):
    store = DocumentStorage(temp_storage_path)
    doc = {"name": "Alice"}
    doc_id = store.insert(doc)
    assert isinstance(doc_id, str)
    loaded = store.get(doc_id)
    assert loaded["name"] == "Alice"
    assert loaded["_id"] == doc_id

def test_insert_invalid_type(temp_storage_path):
    store = DocumentStorage(temp_storage_path)
    with pytest.raises(InvalidDocumentError):
        store.insert(["invalid"])

def test_update_and_get(temp_storage_path):
    store = DocumentStorage(temp_storage_path)
    doc_id = store.insert({"name": "Bob"})
    success = store.update(doc_id, {"age": 30})
    assert success
    updated = store.get(doc_id)
    assert updated["age"] == 30

def test_update_invalid_type(temp_storage_path):
    store = DocumentStorage(temp_storage_path)
    doc_id = store.insert({"name": "Test"})
    with pytest.raises(InvalidDocumentError):
        store.update(doc_id, "not-a-dict")

def test_delete(temp_storage_path):
    store = DocumentStorage(temp_storage_path)
    doc_id = store.insert({"name": "Charlie"})
    assert store.get(doc_id) is not None
    deleted = store.delete(doc_id)
    assert deleted
    assert store.get(doc_id) is None

def test_list_documents(temp_storage_path):
    store = DocumentStorage(temp_storage_path)
    store.insert({"name": "Doc1"})
    store.insert({"name": "Doc2"})
    all_docs = store.list()
    assert len(all_docs) == 2
    names = [doc["name"] for doc in all_docs]
    assert "Doc1" in names
    assert "Doc2" in names

def test_load_invalid_json_raises(temp_storage_path):
    with open(temp_storage_path, "w") as f:
        f.write("not-json")
    with pytest.raises(StorageError):
        DocumentStorage(temp_storage_path)

def test_duplicate_id_insert_raises(temp_storage_path):
    store = DocumentStorage(temp_storage_path)
    doc = {"_id": "fixed-id", "name": "Alice"}
    store.insert(doc)
    with pytest.raises(DuplicateIDError):
        store.insert({"_id": "fixed-id", "name": "Bob"})


def test_json_file_format_after_insert(temp_storage_path):
    store = DocumentStorage(temp_storage_path)
    doc_id = store.insert({"name": "VaultDoc"})

    # Read raw JSON from file
    with open(temp_storage_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    assert isinstance(raw_data, dict)
    assert doc_id in raw_data
    assert raw_data[doc_id]["name"] == "VaultDoc"
    assert raw_data[doc_id]["_id"] == doc_id

def test_atomic_write_failure_does_not_corrupt_file(temp_storage_path):
    store = DocumentStorage(temp_storage_path)
    original_doc = {"name": "SafeDoc"}
    doc_id = store.insert(original_doc)

    # Simulate failure on second insert during os.replace()
    with patch("vaultdb.storage.os.replace", side_effect=Exception("Simulated crash")):
        with pytest.raises(StorageError):
            store.insert({"name": "CrashDoc"})

    # Ensure original data is still intact
    with open(temp_storage_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert doc_id in data
        assert data[doc_id]["name"] == "SafeDoc"

def test_insert_does_not_overwrite_existing_doc(temp_storage_path):
    store = DocumentStorage(temp_storage_path)
    original = {"_id": "safe-id", "name": "Original"}
    store.insert(original)

    with pytest.raises(DuplicateIDError):
        store.insert({"_id": "safe-id", "name": "Malicious"})

    # Confirm original is still intact
    fetched = store.get("safe-id")
    assert fetched["name"] == "Original"

@pytest.mark.skip(reason="To be added in Phase 2 after encryption")
def test_large_document_insert():
    pass




