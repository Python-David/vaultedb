import json
import subprocess
import tempfile
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vaultdb import VaultDB

def create_test_vault(doc_count=3, app_name=None):
    tf = tempfile.NamedTemporaryFile(suffix=".vault", delete=False)
    path = tf.name
    tf.close()
    if os.path.exists(path): os.remove(path)

    vault = VaultDB.open(path, "testpass")
    for i in range(doc_count):
        vault.insert({"_id": f"doc-{i}", "field": f"value-{i}"})
    return path

def run_cli(args):
    result = subprocess.run(
        ["python", "-m", "vaultdb.cli"] + args,
        capture_output=True,
        text=True
    )
    return result

# Functional Tests
def test_inspect_basic_output():
    path = create_test_vault()
    result = run_cli(["inspect", path])
    assert "VaultDB Inspector" in result.stdout
    assert "Document Count: 3" in result.stdout
    os.remove(path)

def test_inspect_max_ids():
    path = create_test_vault(doc_count=5)
    result = run_cli(["inspect", path, "--max-ids", "2"])
    assert "first 2" in result.stdout
    assert "... and 3 more" in result.stdout
    os.remove(path)

def test_inspect_all_ids():
    path = create_test_vault(doc_count=4)
    result = run_cli(["inspect", path, "--max-ids", "10"])
    assert "... and" not in result.stdout
    os.remove(path)

def test_inspect_json_output():
    path = create_test_vault()
    result = run_cli(["inspect", path, "--json"])
    data = json.loads(result.stdout)
    assert data["document_count"] == 3
    assert data["salt"]
    assert isinstance(data["document_ids"], list)
    os.remove(path)

def test_inspect_quiet_mode():
    path = create_test_vault()
    result = run_cli(["inspect", path, "--quiet"])
    assert "VaultDB Inspector" not in result.stdout
    assert "📁" not in result.stdout
    os.remove(path)

def test_inspect_json_quiet():
    path = create_test_vault()
    result = run_cli(["inspect", path, "--json", "--quiet"])
    data = json.loads(result.stdout)
    assert data["file"].endswith(".vault")
    os.remove(path)

# Edge Case Tests
def test_inspect_nonexistent_file():
    result = run_cli(["inspect", "nonexistent.vault"])
    assert result.returncode != 0
    assert "No such file" in result.stderr

def test_inspect_invalid_json_file():
    with tempfile.NamedTemporaryFile(suffix=".vault", delete=False) as tf:
        tf.write(b"not a json file")
        path = tf.name
    result = run_cli(["inspect", path])
    assert result.returncode != 0
    assert "Storage error" in result.stderr
    os.remove(path)

def test_inspect_negative_max_ids():
    path = create_test_vault()
    result = run_cli(["inspect", path, "--max-ids", "-3"])
    assert result.returncode != 0
    assert "Validation error" in result.stderr
    os.remove(path)

def test_inspect_empty_vault():
    path = create_test_vault(doc_count=0)
    result = run_cli(["inspect", path])
    assert "Document Count: 0" in result.stdout
    os.remove(path)

# Security Tests
def test_salt_is_not_truncated_in_json():
    path = create_test_vault()
    result = run_cli(["inspect", path, "--json"])
    data = json.loads(result.stdout)
    assert len(data["salt"]) >= 22  # base64 encoded 16 bytes = 22 chars
    os.remove(path)

def test_app_name_null_if_missing():
    path = create_test_vault()
    result = run_cli(["inspect", path, "--json"])
    data = json.loads(result.stdout)
    assert data["app_name"] is None
    os.remove(path)

def test_inspect_does_not_include_plaintext_fields():
    path = create_test_vault()
    result = run_cli(["inspect", path])
    assert "value-0" not in result.stdout
    assert "field" not in result.stdout
    os.remove(path)
