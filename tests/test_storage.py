import json
import re
import tempfile
import os
from datetime import datetime, timezone

import pytest
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vaultdb.storage import DocumentStorage
from vaultdb.errors import InvalidDocumentError, DuplicateIDError, StorageError


@pytest.fixture
def temp_storage_path():
    with tempfile.NamedTemporaryFile(suffix=".vault", delete=False) as tf:
        yield tf.name
    os.remove(tf.name)

def test_insert_and_get(temp_storage_path):
    store = DocumentStorage(temp_storage_path, app_name="TestApp")
    doc = {"name": "Alice"}
    doc_id = store.insert(doc)
    assert isinstance(doc_id, str)
    loaded = store.get(doc_id)
    assert loaded["name"] == "Alice"
    assert loaded["_id"] == doc_id

def test_metadata_written(temp_storage_path):
    store = DocumentStorage(temp_storage_path, app_name="MyJournal")
    store.insert({"title": "First Entry"})

    with open(temp_storage_path, "r") as f:
        data = json.load(f)
        assert "_meta" in data
        assert data["_meta"]["vault_version"] == "1.0.0"
        assert "created_at" in data["_meta"]
        assert data["_meta"]["app_name"] == "MyJournal"
        assert "documents" in data

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

    with open(temp_storage_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    assert isinstance(raw_data, dict)
    assert "_meta" in raw_data
    assert "documents" in raw_data
    assert doc_id in raw_data["documents"]
    assert raw_data["documents"][doc_id]["name"] == "VaultDoc"
    assert raw_data["documents"][doc_id]["_id"] == doc_id

def test_atomic_write_failure_does_not_corrupt_file(temp_storage_path):
    store = DocumentStorage(temp_storage_path)
    original_doc = {"name": "SafeDoc"}
    doc_id = store.insert(original_doc)

    with patch("vaultdb.storage.os.replace", side_effect=Exception("Simulated crash")):
        with pytest.raises(StorageError):
            store.insert({"name": "CrashDoc"})

    with open(temp_storage_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert doc_id in data["documents"]
        assert data["documents"][doc_id]["name"] == "SafeDoc"

def test_legacy_file_format_raises_storage_error(temp_storage_path):
    # Write legacy export_format (no _meta, no documents key)
    legacy_data = {
        "legacy-id": {"_id": "legacy-id", "content": "legacy"}
    }
    with open(temp_storage_path, "w") as f:
        json.dump(legacy_data, f)

    # Expect a StorageError when loading invalid export_format
    with pytest.raises(StorageError, match="Vault file is not in supported export_format"):
        DocumentStorage(temp_storage_path)

def test_meta_fields_are_protected(temp_storage_path):
    store = DocumentStorage(temp_storage_path, app_name="MetaApp")
    with pytest.raises(RuntimeError, match=re.escape("'vault_version' is read-only metadata")):
        store.meta["vault_version"] = "2.0.0"
    with pytest.raises(RuntimeError, match=re.escape("'created_at' is read-only metadata")):
        store.meta.update({"created_at": "2099-01-01T00:00:00Z"})

def test_created_at_is_recent_and_iso8601(temp_storage_path):
    store = DocumentStorage(temp_storage_path, app_name="TimeTest")
    created_at_str = store.meta["created_at"]
    created_at = datetime.fromisoformat(created_at_str)
    now = datetime.now(timezone.utc)
    delta = abs((now - created_at).total_seconds())
    assert delta < 5  # within 5 seconds of now

def test_metadata_without_app_name(temp_storage_path):
    store = DocumentStorage(temp_storage_path)
    assert "app_name" not in store.meta

def test_meta_structure_on_first_insert(temp_storage_path):
    store = DocumentStorage(temp_storage_path, app_name="VaultNotes")
    store.insert({"note": "hello"})
    with open(temp_storage_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert set(data.keys()) == {"_meta", "documents"}
    assert isinstance(data["_meta"]["created_at"], str)
    assert data["_meta"]["vault_version"] == "1.0.0"
    assert data["_meta"]["app_name"] == "VaultNotes"

def test_meta_allows_custom_fields(temp_storage_path):
    store = DocumentStorage(temp_storage_path, app_name="CustomMetaApp")
    store.meta["label"] = "project-alpha"
    store.meta.update({"env": "staging"})
    assert store.meta["label"] == "project-alpha"
    assert store.meta["env"] == "staging"
