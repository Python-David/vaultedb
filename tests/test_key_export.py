import os
import json
import base64
import tempfile

import pytest
import sys

from vaultedb.encrypted_storage import ExportFormat

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vaultedb import vaultedb

@pytest.fixture
def temp_vault_path():
    with tempfile.NamedTemporaryFile(suffix=".vault", delete=True) as tf:
        path = tf.name
    # Remove the file so vaultedb thinks it's a fresh start
    if os.path.exists(path):
        os.remove(path)
    yield path

def test_export_key_default_returns_dict(temp_vault_path):
    vault = vaultedb.open(temp_vault_path, "hunter2")
    result = vault.export_key()
    assert isinstance(result, dict)
    assert set(result.keys()) == {"key", "salt", "vault_version"}
    base64.urlsafe_b64decode(result["key"].encode())
    base64.urlsafe_b64decode(result["salt"].encode())

def test_export_key_explicit_dict_matches_default(temp_vault_path):
    vault = vaultedb.open(temp_vault_path, "hunter2")
    default = vault.export_key()
    explicit = vault.export_key(export_format=ExportFormat.DICT)
    assert explicit == default

def test_export_key_json_writes_file_and_returns_path(temp_vault_path):
    vault = vaultedb.open(temp_vault_path, "hunter2")
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    filepath = temp_file.name
    temp_file.close()
    os.remove(filepath)  # allow vaultedb to write
    returned_path = vault.export_key(export_format=ExportFormat.JSON, filepath=filepath)
    expected = filepath + ".vaultkey"
    assert returned_path == expected
    assert os.path.exists(returned_path)
    os.remove(returned_path)

def test_export_key_json_respects_extension_and_returns_path(temp_vault_path):
    vault = vaultedb.open(temp_vault_path, "hunter2")
    filepath = tempfile.NamedTemporaryFile(suffix=".vaultkey", delete=False).name
    os.remove(filepath)
    returned_path = vault.export_key(export_format=ExportFormat.JSON, filepath=filepath)
    assert returned_path == filepath
    assert os.path.exists(returned_path)
    assert not os.path.exists(filepath + ".vaultkey")
    os.remove(filepath)

def test_export_key_json_no_filepath_raises(temp_vault_path):
    vault = vaultedb.open(temp_vault_path, "hunter2")
    with pytest.raises(ValueError):
        vault.export_key(export_format=ExportFormat.JSON)

def test_export_key_unsupported_format_raises(temp_vault_path):
    vault = vaultedb.open(temp_vault_path, "hunter2")
    with pytest.raises(ValueError):
        vault.export_key(filepath=temp_vault_path, export_format="xml")

def test_export_key_before_open_raises():
    dummy = object.__new__(vaultedb)
    with pytest.raises(RuntimeError):
        dummy.export_key()

def test_export_key_file_contents_match_dict(temp_vault_path):
    vault = vaultedb.open(temp_vault_path, "hunter2")
    dict_result = vault.export_key()
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    filepath = temp_file.name
    temp_file.close()
    os.remove(filepath)
    vault.export_key(export_format=ExportFormat.JSON, filepath=filepath)
    with open(filepath + ".vaultkey", "r") as f:
        loaded = json.load(f)
    assert loaded == dict_result
    os.remove(filepath + ".vaultkey")

def test_export_key_dict_is_deterministic(temp_vault_path):
    vault = vaultedb.open(temp_vault_path, "hunter2")
    first = vault.export_key()
    second = vault.export_key()
    assert first == second

def test_export_key_rederived_key_matches(temp_vault_path):
    vault = vaultedb.open(temp_vault_path, "hunter2")
    data = vault.export_key()
    decoded = base64.urlsafe_b64decode(data["key"].encode())
    assert decoded == vault.key