"""
Example usage of VaultDB's EncryptedStorage
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vaultdb.encrypted_storage import EncryptedStorage
from vaultdb.crypto import generate_key, generate_salt

# Setup
vault_path = "temp_example.vault"

# Clean slate: delete vault file from previous runs
if os.path.exists(vault_path):
    os.remove(vault_path)

# Generate fresh key
passphrase = "secret-passphrase"
salt = generate_salt()
key = generate_key(passphrase, salt)
vault = EncryptedStorage(vault_path, key)

# Insert
doc_id = vault.insert({"name": "Alice", "email": "alice@example.com"})
print("Inserted ID:", doc_id)

# Retrieve
retrieved = vault.get(doc_id)
print("Retrieved:", retrieved)

# Update
vault.update(doc_id, {"role": "admin"})

# Confirm update
print("Updated:", vault.get(doc_id))

# 🔍 Find documents
results = vault.find({"name": "Alice"})
print("Find by name=Alice:", results)

# Delete
# vault.delete(doc_id)
# print("After deletion:", vault.get(doc_id))

# Inspect raw file (optional for demo)
with open(vault_path, "r") as f:
    print("\nRaw on disk:\n", f.read())
