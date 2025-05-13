import os
import json
import sys
import tempfile
import pytest
import base64
import logging

from cryptography.fernet import Fernet

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vaultdb.encrypted_storage import EncryptedStorage
from vaultdb.logging import VaultAuditLog
from vaultdb.crypto import generate_key, generate_salt
from vaultdb.errors import CryptoError


@pytest.fixture
def temp_vault_and_log():
    path = tempfile.mktemp(suffix=".vault")
    log_path = path.replace(".vault", ".vaultlog")
    yield path, log_path
    for p in (path, log_path):
        if os.path.exists(p):
            os.remove(p)

@pytest.fixture
def key():
    return generate_key("test-passphrase", generate_salt())


# === VaultAuditLog tests ===

def test_log_writes_encrypted_line(temp_vault_and_log, key):
    _, log_path = temp_vault_and_log
    log = VaultAuditLog(log_path, key)
    log.log("insert", "doc1")
    with open(log_path, "rb") as f:
        lines = f.readlines()
    assert len(lines) == 1
    assert isinstance(lines[0], bytes)


def test_entries_returns_decrypted_entries(temp_vault_and_log, key):
    _, log_path = temp_vault_and_log
    log = VaultAuditLog(log_path, key)
    log.log("insert", "doc1")
    log.log("get", "doc2")
    entries = log.entries()
    assert len(entries) == 2
    assert entries[0]["op"] == "insert"
    assert entries[1]["_id"] == "doc2"


def test_tail_returns_last_n_entries(temp_vault_and_log, key):
    _, log_path = temp_vault_and_log
    log = VaultAuditLog(log_path, key)
    for i in range(5):
        log.log("get", f"doc{i}")
    tail = log.tail(2)
    assert len(tail) == 2
    assert tail[-1]["_id"] == "doc4"


def test_log_accepts_metadata(temp_vault_and_log, key):
    _, log_path = temp_vault_and_log
    log = VaultAuditLog(log_path, key)
    log.log("insert", "doc-meta", {"source": "MyApp"})
    entry = log.entries()[0]
    assert entry["meta"]["source"] == "MyApp"


def test_export_json_writes_file(temp_vault_and_log, key):
    _, log_path = temp_vault_and_log
    log = VaultAuditLog(log_path, key)
    log.log("insert", "doc3")
    export_path = log_path + ".json"
    log.export_json(export_path)
    assert os.path.exists(export_path)
    with open(export_path) as f:
        data = json.load(f)
        assert isinstance(data, list)
        assert data[0]["_id"] == "doc3"
    os.remove(export_path)


def test_log_handles_write_error_with_hook(temp_vault_and_log, key):
    _, log_path = temp_vault_and_log
    errors = []
    def err_hook(e): errors.append(str(e))
    log = VaultAuditLog(log_path, key, on_log_error=err_hook)
    original_open = open
    def broken_open(*args, **kwargs): raise IOError("fail")
    try:
        __builtins__["open"] = broken_open
        log.log("insert", "fail")
    finally:
        __builtins__["open"] = original_open
    assert any("fail" in e for e in errors)


def test_log_handles_write_error_silently_by_default(temp_vault_and_log, key, caplog):
    _, log_path = temp_vault_and_log
    log = VaultAuditLog(log_path, key)
    original_open = open
    def broken_open(*args, **kwargs): raise IOError("boom")
    try:
        __builtins__["open"] = broken_open
        with caplog.at_level(logging.WARNING):
            log.log("insert", "fail")
    finally:
        __builtins__["open"] = original_open
    assert any("VaultAuditLog failed to log operation" in r.message for r in caplog.records)


def test_wrong_key_fails_to_decrypt_entries(temp_vault_and_log, key):
    _, log_path = temp_vault_and_log
    log = VaultAuditLog(log_path, key)
    log.log("insert", "secret")
    wrong_key = Fernet.generate_key()
    log2 = VaultAuditLog(log_path, wrong_key)
    with pytest.raises(CryptoError):
        log2.entries()


def test_invalid_log_line_raises_cryptoerror(temp_vault_and_log, key):
    _, log_path = temp_vault_and_log
    with open(log_path, "wb") as f:
        f.write(b"corrupt\n")
    log = VaultAuditLog(log_path, key)
    with pytest.raises(CryptoError):
        log.entries()


def test_missing_log_file_returns_empty_list(key):
    path = tempfile.mktemp(suffix=".vaultlog")
    if os.path.exists(path): os.remove(path)
    log = VaultAuditLog(path, key)
    assert log.entries() == []


def test_log_file_created_with_permissions(temp_vault_and_log, key):
    _, log_path = temp_vault_and_log
    log = VaultAuditLog(log_path, key)
    log.log("insert", "secure")
    mode = os.stat(log_path).st_mode & 0o777
    assert mode == 0o600


# === EncryptedStorage + Logging integration ===

def test_encrypted_storage_logs_insert(temp_vault_and_log):
    path, _ = temp_vault_and_log
    vault = EncryptedStorage.open(path, "hunter2", enable_logging=True)
    doc_id = vault.insert({"name": "TestUser"})
    logs = vault.get_audit_log().entries()
    assert any(e["op"] == "insert" and e["_id"] == doc_id for e in logs)


def test_encrypted_storage_logs_get(temp_vault_and_log):
    path, _ = temp_vault_and_log
    vault = EncryptedStorage.open(path, "hunter2", enable_logging=True)
    doc_id = vault.insert({"name": "Alice"})
    _ = vault.get(doc_id)
    logs = vault.get_audit_log().entries()
    assert any(e["op"] == "get" and e["_id"] == doc_id for e in logs)


def test_encrypted_storage_logs_update(temp_vault_and_log):
    path, _ = temp_vault_and_log
    vault = EncryptedStorage.open(path, "hunter2", enable_logging=True)
    doc_id = vault.insert({"name": "Bob"})
    vault.update(doc_id, {"city": "Lagos"})
    logs = vault.get_audit_log().entries()
    assert any(e["op"] == "update" and e["_id"] == doc_id and e["meta"]["city"] == "Lagos" for e in logs)


def test_encrypted_storage_logs_delete(temp_vault_and_log):
    path, _ = temp_vault_and_log
    vault = EncryptedStorage.open(path, "hunter2", enable_logging=True)
    doc_id = vault.insert({"name": "Charlie"})
    vault.delete(doc_id)
    logs = vault.get_audit_log().entries()
    assert any(e["op"] == "delete" and e["_id"] == doc_id for e in logs)


def test_logging_does_not_break_insert_on_log_failure(temp_vault_and_log, monkeypatch):
    path, _ = temp_vault_and_log
    vault = EncryptedStorage.open(path, "hunter2", enable_logging=True)
    monkeypatch.setattr("vaultdb.logging.VaultAuditLog.log", lambda *a, **kw: (_ for _ in ()).throw(IOError("boom")))
    doc_id = vault.insert({"name": "SafeInsert"})
    assert doc_id


def test_logging_respects_enable_flag(temp_vault_and_log):
    path, log_path = temp_vault_and_log
    _ = EncryptedStorage.open(path, "hunter2", enable_logging=False)
    assert not os.path.exists(log_path)


def test_get_audit_log_raises_if_disabled(temp_vault_and_log):
    path, _ = temp_vault_and_log
    vault = EncryptedStorage.open(path, "hunter2", enable_logging=False)
    with pytest.raises(RuntimeError):
        vault.get_audit_log()


def test_audit_log_export_and_view_in_app(temp_vault_and_log):
    path, _ = temp_vault_and_log
    vault = EncryptedStorage.open(path, "hunter2", enable_logging=True)
    vault.insert({"title": "Day 1"})
    export_path = path.replace(".vault", "_logs.json")
    vault.get_audit_log().export_json(export_path)
    with open(export_path, "r") as f:
        logs = json.load(f)
    assert isinstance(logs, list)
    assert logs[0]["op"] == "insert"
    os.remove(export_path)


def test_insert_and_log_can_be_replayed(temp_vault_and_log):
    path, _ = temp_vault_and_log
    vault = EncryptedStorage.open(path, "hunter2", enable_logging=True)
    doc_id = vault.insert({"mood": "happy"})
    logs = vault.get_audit_log().entries()
    assert logs[-1]["op"] == "insert"
    assert logs[-1]["_id"] == doc_id
