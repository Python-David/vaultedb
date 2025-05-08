import json
import os
import tempfile
import pytest
import base64
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vaultdb import VaultDB
from vaultdb.errors import CryptoError, StorageError
from vaultdb.storage import DocumentStorage

@pytest.fixture
def temp_vault_path():
    with tempfile.NamedTemporaryFile(suffix=".vault", delete=True) as tf:
        path = tf.name
    # Remove the file so VaultDB thinks it's a fresh start
    if os.path.exists(path):
        os.remove(path)
    yield path

def test_from_passphrase_creates_salt_meta(temp_vault_path):
    vault = VaultDB.open(temp_vault_path, "securepass")
    store = DocumentStorage(temp_vault_path)
    assert "salt" in store.meta
    assert store.salt is not None

def test_from_passphrase_reopens_existing_vault(temp_vault_path):
    vault1 = VaultDB.open(temp_vault_path, "reopen-test")
    vault1.insert({"_id": "test-doc", "msg": "hello"})

    vault2 = VaultDB.open(temp_vault_path, "reopen-test")
    doc = vault2.get("test-doc")
    assert doc["msg"] == "hello"

def test_from_passphrase_raises_on_missing_salt(temp_vault_path):
    with open(temp_vault_path, "w", encoding="utf-8") as f:
        f.write('{"_meta": {"vault_version": "1.0.0", "created_at": "now"}, "documents": {}}')
    with pytest.raises(CryptoError, match="missing 'salt' metadata"):
        VaultDB.open(temp_vault_path, "oops")

def test_from_passphrase_raises_on_invalid_extension():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        path = tf.name
    with pytest.raises(ValueError, match="must use the .vault extension"):
        VaultDB.open(path, "nope")
    os.remove(path)

def test_from_passphrase_fails_on_invalid_json(temp_vault_path):
    with open(temp_vault_path, "w", encoding="utf-8") as f:
        f.write("this is not json")
    with pytest.raises(StorageError, match="VaultDB failed to load this file"):
        VaultDB.open(temp_vault_path, "invalid-json")


def test_from_passphrase_fails_on_empty_file(temp_vault_path):
    open(temp_vault_path, "w").close()  # create empty file
    with pytest.raises(CryptoError, match="missing 'salt' metadata"):
        VaultDB.open(temp_vault_path, "emptyfile")

def test_from_passphrase_rejects_empty_passphrase(temp_vault_path):
    with pytest.raises(ValueError, match="Passphrase must not be empty"):
        VaultDB.open(temp_vault_path, "")


# def test_from_passphrase_raises_on_invalid_base64_salt(temp_vault_path):
#     # Corrupt the base64 salt manually
#     store = VaultDB.from_passphrase(temp_vault_path, "ok")
#     with open(temp_vault_path, "r+", encoding="utf-8") as f:
#         data = json.load(f)
#         data["_meta"]["salt"] = "!!!notbase64"
#         f.seek(0)
#         json.dump(data, f)
#         f.truncate()
#     with pytest.raises(CryptoError, match="Failed to read existing vault or salt"):
#         VaultDB.from_passphrase(temp_vault_path, "ok")
#
#
# def test_from_passphrase_salt_differs_between_vaults():
#     with tempfile.NamedTemporaryFile(suffix=".vault", delete=False) as tf1, \
#          tempfile.NamedTemporaryFile(suffix=".vault", delete=False) as tf2:
#         p1, p2 = tf1.name, tf2.name
#
#     VaultDB.from_passphrase(p1, "pw")
#     VaultDB.from_passphrase(p2, "pw")
#
#     s1 = DocumentStorage(p1).salt
#     s2 = DocumentStorage(p2).salt
#     os.remove(p1)
#     os.remove(p2)
#     assert s1 != s2
