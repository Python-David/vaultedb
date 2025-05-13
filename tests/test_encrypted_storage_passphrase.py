import json
import os
import tempfile
import pytest
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vaultedb import vaultedb
from vaultedb.errors import CryptoError
from vaultedb.storage import DocumentStorage

@pytest.fixture
def temp_vault_path():
    with tempfile.NamedTemporaryFile(suffix=".vault", delete=True) as tf:
        path = tf.name
    # Remove the file so vaultedb thinks it's a fresh start
    if os.path.exists(path):
        os.remove(path)
    yield path

# === Core Functionality ===

def test_open_creates_salt_and_meta(temp_vault_path):
    vault = vaultedb.open(temp_vault_path, "securepass")
    store = DocumentStorage(temp_vault_path)
    assert "salt" in store.meta
    assert store.salt is not None


def test_open_reopens_existing_vault_and_decrypts(temp_vault_path):
    vault1 = vaultedb.open(temp_vault_path, "reopen-test")
    vault1.insert({"_id": "test-doc", "msg": "hello"})

    vault2 = vaultedb.open(temp_vault_path, "reopen-test")
    doc = vault2.get("test-doc")
    assert doc["msg"] == "hello"


# === Input Validation & Edge Cases ===

def test_open_raises_on_missing_salt(temp_vault_path):
    with open(temp_vault_path, "w", encoding="utf-8") as f:
        f.write('{"_meta": {"vault_version": "1.0.0", "created_at": "now"}, "documents": {}}')
    with pytest.raises(CryptoError, match="vaultedb failed to load this file"):
        vaultedb.open(temp_vault_path, "oops")


def test_open_raises_on_invalid_extension():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        path = tf.name
    with pytest.raises(ValueError, match="must use the .vault extension"):
        vaultedb.open(path, "nope")
    os.remove(path)


def test_open_fails_on_invalid_json(temp_vault_path):
    with open(temp_vault_path, "w", encoding="utf-8") as f:
        f.write("this is not json")
    with pytest.raises(CryptoError, match="vaultedb failed to load this file"):
        vaultedb.open(temp_vault_path, "invalid-json")


def test_open_fails_on_empty_file(temp_vault_path):
    open(temp_vault_path, "w").close()
    with pytest.raises(CryptoError, match="vaultedb failed to load this file"):
        vaultedb.open(temp_vault_path, "emptyfile")


def test_open_rejects_empty_passphrase(temp_vault_path):
    with pytest.raises(ValueError, match="Passphrase must not be empty"):
        vaultedb.open(temp_vault_path, "")


def test_open_raises_on_invalid_base64_salt(temp_vault_path):
    vault = vaultedb.open(temp_vault_path, "ok")
    with open(temp_vault_path, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data["_meta"]["salt"] = "!!!notbase64"
        f.seek(0)
        json.dump(data, f)
        f.truncate()
    with pytest.raises(CryptoError, match="vaultedb failed to load this file"):
        vaultedb.open(temp_vault_path, "ok")


# === Security Guarantees ===

def test_cross_vault_decryption_fails_with_same_passphrase():
    with tempfile.NamedTemporaryFile(suffix=".vault", delete=True) as tf1, \
         tempfile.NamedTemporaryFile(suffix=".vault", delete=True) as tf2:
        p1, p2 = tf1.name, tf2.name

    for p in (p1, p2):
        if os.path.exists(p): os.remove(p)

    vault1 = vaultedb.open(p1, "pw")
    vault2 = vaultedb.open(p2, "pw")

    vault1.insert({"_id": "shared-id", "msg": "vault1"})

    s1 = DocumentStorage(p1).salt
    s2 = DocumentStorage(p2).salt
    assert s1 != s2

    encrypted_blob = DocumentStorage(p1).data["shared-id"]
    vault2.store.insert(encrypted_blob)

    with pytest.raises(CryptoError):
        vault2.get("shared-id")

    os.remove(p1)
    os.remove(p2)