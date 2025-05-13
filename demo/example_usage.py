"""
🔐 VaultDB: Example Usage & Feature Walkthrough

This script walks you through the core features of VaultDB — an encrypted, file-based document store
that protects your data with zero config and strong defaults.

Think of VaultDB as "SQLite for secrets" — everything is private, secure, and portable by default.
"""

import os
from vaultdb import VaultDB
from vaultdb.errors import CryptoError
from pprint import pprint
from pathlib import Path

# 💥 Start fresh by deleting old vault files for repeatable demo
for base in ["example", "vault1", "vault2", "example-logged"]:
    for ext in [".vault", ".vaultlog"]:
        f = f"{base}{ext}"
        if os.path.exists(f):
            os.remove(f)


print("\n=== 🚀 Welcome to VaultDB ===")
print("VaultDB is a local, encrypted database for storing sensitive documents (like JSON objects).")
print("Each vault is a single .vault file. All data is encrypted using a key derived from a passphrase.")

print("\n=== 🔐 Step 1: Create or Open a Vault ===")
vault = VaultDB.open("example.vault", "vaultdb-demo-pass")
print("We just created a new encrypted vault file: 'example.vault'")
print("The encryption key is derived from the passphrase you provide — no keys to manage manually!")

print("\n=== ✍️ Step 2: Insert Documents into the Vault ===")
vault.insert({"_id": "user-alice", "email": "alice@example.com", "role": "admin"})
vault.insert({"_id": "user-bob", "email": "bob@example.com", "role": "viewer"})
print("Inserted two documents. These are immediately encrypted and saved to disk — no plaintext is stored.")

print("\n=== 🔍 Step 3: Query Encrypted Data ===")
doc = vault.get("user-alice")
print("Get by ID:")
pprint(doc)

admins = vault.find({"role": "admin"})
print("Find by field (role=admin):")
pprint(admins)

print("\n=== 📦 Step 4: See the Raw Vault File ===")
vault_raw = Path("example.vault").read_text()
print("Let’s peek at the .vault file on disk. Here’s what it looks like:")
print(vault_raw[:500] + "\n...\n(truncated)")
print("Notice: No sensitive data is visible. All content is encrypted.")

print("\n=== 🧪 Step 5: Vault Isolation Demo ===")
print("Now we’ll simulate a copy-paste attack. Can one vault read another vault’s data?")
vault1 = VaultDB.open("vault1.vault", "hunter2")
vault2 = VaultDB.open("vault2.vault", "hunter2")

vault1.insert({"_id": "secret", "msg": "top secret"})

# simulate data theft: copy encrypted blob from vault1 to vault2
vault2.store.insert(vault1.store.data["secret"])

print("We copied an encrypted blob from vault1 to vault2, both using same passphrase.")
print("Now we try to decrypt it using vault2:")

try:
    vault2.get("secret")
except CryptoError:
    print("✅ Decryption failed — VaultDB ensures that even with same passphrase, each vault is isolated.")
    print("This protects against insider attacks, blob leaks, and key reuse risks.")

print("\n=== 🪵 Step 6: Audit Logging (Optional Feature) ===")
print("VaultDB can also log every action securely, with encrypted audit logs.")
vault = VaultDB.open("example-logged.vault", "vaultdb-demo-pass", enable_logging=True)
doc_id = vault.insert({"_id": "log1", "msg": "audit test"})
vault.get(doc_id)

log = vault.get_audit_log()
print("Here’s what the audit log looks like (decrypted):")
pprint(log.entries())

print("\n=== 🗝️ Step 7: Export Key + Salt for Backup ===")
key_blob = vault.export_key()
pprint(key_blob)

print("\n⚠️ WARNING: If you lose this key+salt, you lose access to your vault.")
print("VaultDB doesn't store your key — it's YOUR responsibility to back this up securely.")

print("\n🎉 Done! You’ve seen:")
print("- How to create an encrypted vault")
print("- How to insert/query documents securely")
print("- How VaultDB prevents cross-vault attacks")
print("- How audit logging works")
print("- How to export your key securely")

print("\nVaultDB = End-to-End Privacy + Developer Simplicity.")
