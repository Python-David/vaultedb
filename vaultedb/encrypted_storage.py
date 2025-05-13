import base64
import json
import os
import sys
import warnings
from enum import Enum
from typing import Optional, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vaultedb.storage import DocumentStorage
from vaultedb.crypto import encrypt_document, decrypt_document, CryptoError, generate_salt, generate_key
from vaultedb.errors import InvalidDocumentError, DuplicateIDError
from vaultedb.logging import VaultAuditLog
import uuid


class ExportFormat(str, Enum):
    DICT = "dict"
    JSON = "json"


class EncryptedStorage:
    """
    Wraps DocumentStorage to provide transparent encryption/decryption of documents.

    Documents are encrypted before writing to disk and decrypted on read.
    The _id field is stored in plaintext to enable efficient lookup.
    """

    def __init__(self, path: str, key: bytes, audit_log: Optional[VaultAuditLog] = None):
        if not path.endswith(".vault"):
            warnings.warn(
                "It's recommended to use a `.vault` extension for encrypted vaultedb files.",
                UserWarning
            )
        self.key = key
        self.store = DocumentStorage(path)
        self.audit_log = audit_log

    def insert(self, doc: dict) -> str:
        if not isinstance(doc, dict):
            raise InvalidDocumentError("Document must be a dictionary.")
        _id = doc.get("_id") or str(uuid.uuid4())
        doc["_id"] = _id  # ensure internal _id matches external
        try:
            encrypted = encrypt_document(doc, self.key)
            result = self.store.insert({"_id": _id, "data": encrypted})
            if self.audit_log:
                try:
                    self.audit_log.log("insert", _id)
                except Exception:
                    pass
            return result
        except DuplicateIDError:
            raise
        except Exception as e:
            raise CryptoError(f"Insertion failed: {e}")

    def get(self, doc_id: str) -> Optional[dict]:
        raw = self.store.get(doc_id)
        if not raw:
            return None
        if "data" not in raw:
            raise CryptoError("Missing encrypted data field.")
        try:
            doc = decrypt_document(raw["data"], self.key)
            if self.audit_log:
                try:
                    self.audit_log.log("get", doc_id)
                except Exception:
                    pass
            return doc
        except Exception as e:
            raise CryptoError(f"Decryption failed on get: {e}")

    def update(self, doc_id: str, updates: dict) -> bool:
        if not isinstance(updates, dict):
            raise InvalidDocumentError("Update must be a dictionary.")
        existing = self.get(doc_id)
        if not existing:
            return False
        existing.update(updates)
        try:
            encrypted = encrypt_document(existing, self.key)
            result = self.store.update(doc_id, {"data": encrypted})
            if result and self.audit_log:
                try:
                    self.audit_log.log("update", doc_id, updates)
                except Exception:
                    pass
            return result
        except Exception as e:
            raise CryptoError(f"Update failed: {e}")

    def delete(self, doc_id: str) -> bool:
        result = self.store.delete(doc_id)
        if result:
            if self.audit_log:
                try:
                    self.audit_log.log("delete", doc_id)
                except Exception:
                    pass
            return True
        return False

    def list(self, strict: bool = True) -> List[dict]:
        """
        Returns all decrypted documents.

        If strict is False, skips documents that fail decryption.
        """
        docs = []
        raw_docs = self.store.list()

        for raw in raw_docs:
            if "data" not in raw:
                if strict:
                    raise CryptoError("Missing encrypted data field in document.")
                continue

            try:
                doc = decrypt_document(raw["data"], self.key)
                docs.append(doc)
            except Exception as e:
                if strict:
                    raise CryptoError(f"Decryption failed during list operation: {e}")
                # When not in strict mode, skip this document
                continue

        return docs

    def find(self, filter: dict) -> List[dict]:
        """
        Finds documents matching all key-value pairs in the given filter.

        Args:
            filter (dict): A dictionary of field-value pairs to match.
                           Only documents containing all matching fields with equal values will be returned.

        Returns:
            List[dict]: A list of decrypted documents that match the filter.

        Raises:
            InvalidDocumentError: If the filter is not a dictionary.
            CryptoError: If decryption fails or data is malformed and strict mode is enforced.
        """
        if not isinstance(filter, dict):
            raise InvalidDocumentError("Filter must be a dictionary.")

        all_docs = self.list(strict=True)
        results = []

        for doc in all_docs:
            if all(doc.get(k) == v for k, v in filter.items()):
                results.append(doc)

        return results

    @classmethod
    def open(cls, path: str, passphrase: str, enable_logging: bool = False) -> "EncryptedStorage":
        """
        Initializes EncryptedStorage from a passphrase.

        - Loads existing vault and reads embedded salt if present.
        - For new vaults, generates and embeds a salt.
        - Raises CryptoError if an existing vault lacks salt.
        """
        if not passphrase:
            raise ValueError("Passphrase must not be empty. vaultedb requires a non-empty passphrase for encryption.")

        if not path.endswith(".vault"):
            raise ValueError("Vault file must use the .vault extension")

        try:
            if os.path.exists(path):
                probe = DocumentStorage(path)
                if not probe.salt:
                    raise CryptoError("Vault exists but missing 'salt' metadata; cannot derive key.")
                salt = probe.salt
            else:
                salt = generate_salt()
                DocumentStorage(path, app_name=None, salt=salt)

            key = generate_key(passphrase, salt)
            audit_log = None
            if enable_logging:
                log_path = path.replace(".vault", ".vaultlog")
                audit_log = VaultAuditLog(log_path, key)
            return cls(path, key, audit_log=audit_log)

        except Exception as e:
            raise CryptoError(f"vaultedb failed to load this file — {e}") from e

    def get_audit_log(self) -> VaultAuditLog:
        if not self.audit_log:
            raise RuntimeError("Audit logging was not enabled for this vault.")
        return self.audit_log

    def export_key(
            self,
            export_format: ExportFormat = ExportFormat.DICT,
            filepath: Optional[str] = None
    ) -> Optional[dict | str]:
        """
        Export the derived key and salt used for this vault.

        Args:
            export_format: 'dict' (default) returns a Python dict,
                    'json' writes to a `.vaultkey` file
            filepath: File path to write the key export if format='json'.
                      Will auto-append `.vaultkey` if missing.

        Returns:
            dict if format='dict'; None if file is written

        Raises:
            RuntimeError if called before opening the vault
            ValueError if format='json' and no filepath provided
        """
        if not hasattr(self, "store") or not hasattr(self.store, "salt"):
            raise RuntimeError("Vault must be opened before exporting key.")

        export = {
            "key": base64.urlsafe_b64encode(self.key).decode("utf-8"),
            "salt": base64.urlsafe_b64encode(self.store.salt).decode("utf-8"),
            "vault_version": self.store.meta.get("vault_version", "unknown")
        }

        if export_format == ExportFormat.DICT:
            return export

        elif export_format == ExportFormat.JSON:
            if not filepath:
                raise ValueError("Must provide `filepath` when export_format='json'")

            if not filepath.endswith(".vaultkey"):
                filepath += ".vaultkey"

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export, f, indent=2)
            return filepath

        else:
            raise ValueError("Unsupported export_format. Use 'dict' or 'json'.")
