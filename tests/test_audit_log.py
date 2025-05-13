import os
import sys
import tempfile
import json
import stat
import base64
from datetime import datetime
from typing import List

import pytest
from cryptography.fernet import Fernet

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vaultedb.logging import VaultAuditLog
from vaultedb.crypto import generate_salt, generate_key
from vaultedb.errors import CryptoError


@pytest.fixture
def temp_log_path():
    with tempfile.NamedTemporaryFile(suffix=".vaultlog", delete=False) as tf:
        path = tf.name
    os.remove(path)
    yield path
    if os.path.exists(path):
        os.remove(path)

@pytest.fixture
def key():
    return generate_key("audit-test-pass", generate_salt())


# --- CORE FUNCTIONALITY TESTS ---

def test_log_writes_encrypted_line(temp_log_path, key):
    log = VaultAuditLog(temp_log_path, key)
    log.log("insert", "abc123")
    with open(temp_log_path, "rb") as f:
        lines = f.readlines()
    assert len(lines) == 1
    assert isinstance(lines[0], bytes)

def test_entries_returns_decrypted_entries(temp_log_path, key):
    log = VaultAuditLog(temp_log_path, key)
    log.log("insert", "doc1")
    log.log("get", "doc2")
    entries = log.entries()
    assert isinstance(entries, list)
    assert len(entries) == 2
    assert entries[0]["op"] == "insert"
    assert entries[1]["_id"] == "doc2"

def test_tail_returns_last_n_entries(temp_log_path, key):
    log = VaultAuditLog(temp_log_path, key)
    for i in range(5):
        log.log("get", f"id-{i}")
    tail = log.tail(2)
    assert len(tail) == 2
    assert tail[-1]["_id"] == "id-4"

def test_log_accepts_metadata(temp_log_path, key):
    log = VaultAuditLog(temp_log_path, key)
    log.log("insert", "meta-test", {"label": "journal"})
    entry = log.entries()[0]
    assert entry["meta"]["label"] == "journal"

def test_file_permissions_set_on_creation(temp_log_path, key):
    log = VaultAuditLog(temp_log_path, key)
    log.log("insert", "secure")
    mode = stat.S_IMODE(os.lstat(temp_log_path).st_mode)
    assert mode == 0o600


# --- EDGE CASES & FAILURE MODES ---

def test_wrong_key_fails_to_decrypt_entries(temp_log_path, key):
    log1 = VaultAuditLog(temp_log_path, key)
    log1.log("insert", "secret")

    bad_key = Fernet.generate_key()
    log2 = VaultAuditLog(temp_log_path, bad_key)
    with pytest.raises(CryptoError):
        log2.entries()

def test_invalid_line_raises_crypto_error(temp_log_path, key):
    with open(temp_log_path, "wb") as f:
        f.write(b"not-a-token\n")
    log = VaultAuditLog(temp_log_path, key)
    with pytest.raises(CryptoError):
        log.entries()

def test_missing_log_file_returns_empty(key):
    path = tempfile.mktemp(suffix=".vaultlog")
    if os.path.exists(path):
        os.remove(path)
    log = VaultAuditLog(path, key)
    assert log.entries() == []

def test_log_handles_write_error_with_hook(temp_log_path, key):
    captured = []

    def error_hook(exc):
        captured.append(str(exc))

    log = VaultAuditLog(temp_log_path, key, on_log_error=error_hook)
    # Simulate write error by patching open
    original_open = open
    def broken_open(*args, **kwargs):
        raise IOError("disk full")

    try:
        __builtins__["open"] = broken_open
        log.log("insert", "fail")
    finally:
        __builtins__["open"] = original_open

    assert any("disk full" in err for err in captured)

def test_log_handles_write_error_silently_by_default(temp_log_path, key, caplog):
    log = VaultAuditLog(temp_log_path, key)
    original_open = open

    def broken_open(*args, **kwargs):
        raise IOError("boom")

    try:
        __builtins__["open"] = broken_open
        with caplog.at_level("WARNING"):
            log.log("insert", "fail")
    finally:
        __builtins__["open"] = original_open

    assert any("VaultAuditLog failed to log operation" in record.message for record in caplog.records)

def test_tail_more_than_total_returns_all(temp_log_path, key):
    log = VaultAuditLog(temp_log_path, key)
    log.log("insert", "a")
    log.log("insert", "b")
    tail = log.tail(10)
    assert len(tail) == 2


# --- OPTIONAL CHECKS ---

def test_audit_entry_contains_expected_keys(temp_log_path, key):
    log = VaultAuditLog(temp_log_path, key)
    log.log("delete", "zz")
    entry = log.entries()[0]
    assert set(entry.keys()) == {"op", "_id", "at", "meta"}

def test_entry_timestamp_is_iso8601(temp_log_path, key):
    log = VaultAuditLog(temp_log_path, key)
    log.log("get", "timecheck")
    at = log.entries()[0]["at"]
    # Should parse without exception
    parsed = datetime.fromisoformat(at)
    assert parsed.tzinfo is not None
