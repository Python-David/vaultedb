import base64
import json
import os
import tempfile
from datetime import datetime, timezone
from typing import Dict, Optional, List
import uuid
from vaultedb.errors import InvalidDocumentError, DuplicateIDError, StorageError
from vaultedb.config import vaultedb_VERSION


class ProtectedMetaDict(dict):
    """
    A dictionary subclass that protects core vaultedb metadata fields from being overwritten.

    Protected fields:
    - 'created_at': auto-generated timestamp when the vault is first created.
    - 'vault_version': the version of the vaultedb export_format.
    - 'salt': base64-encoded cryptographic salt used for key derivation.

    These fields are critical for the integrity and security of the vault,
    and attempts to modify them after creation will raise a RuntimeError.
    """

    _protected_keys = {"created_at", "vault_version", "salt"}

    def __setitem__(self, key, value):
        if key in self._protected_keys:
            raise RuntimeError(f"'{key}' is read-only metadata")
        super().__setitem__(key, value)

    def update(self, *args, **kwargs):
        for key in dict(*args, **kwargs):
            if key in self._protected_keys:
                raise RuntimeError(f"'{key}' is read-only metadata")
        super().update(*args, **kwargs)



class DocumentStorage:
    """
    Handles loading and saving encrypted documents to disk in JSON export_format.
    Used as the low-level storage engine by vaultedb. Includes metadata for versioning,
    app context, and key derivation salt.

    File schema:
    {
        "_meta": {
            "vault_version": "1.0.0",
            "created_at": "...",
            "app_name": "...",
            "salt": "base64-encoded-salt"
        },
        "documents": {
            "abc123": {"_id": "abc123", "data": "..."}
        }
    }

    Responsibilities:
    - Read/write all documents to a single JSON file
    - Assign unique _id to documents if not provided
    - Persist metadata (_meta) including creation time, app name, and salt
    - Ensure atomicity during write operations
    - Validate input types
    - Support listing all documents
    - Enforce unique _id per document
    """

    def __init__(self, path: str, app_name: Optional[str] = None, salt: Optional[bytes] = None):
        self.path = path
        self.meta: ProtectedMetaDict = ProtectedMetaDict()
        self.data: Dict[str, dict] = {}
        self.salt: Optional[bytes] = None

        # If salt provided and no file exists → initialize new vault with salt
        if salt is not None and not os.path.exists(path):
            self._initialize_meta(app_name, salt)
            self.data = {}
            self._atomic_write()
        else:
            self._load(app_name)

    def _load(self, app_name: Optional[str]):
        if not os.path.exists(self.path):
            self._initialize_meta(app_name)
            self.data = {}
            return

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    self._initialize_meta(app_name)
                    self.data = {}
                    return

                raw = json.loads(content)
                if "_meta" in raw and "documents" in raw:
                    self.meta = ProtectedMetaDict(raw["_meta"])
                    self.data = raw["documents"]

                    salt_b64 = self.meta.get("salt")
                    if salt_b64:
                        import base64
                        self.salt = base64.urlsafe_b64decode(salt_b64.encode("utf-8"))
                    else:
                        self.salt = None  # Vault created without salt? Should raise if used for passphrase
                else:
                    raise StorageError("Vault file is not in supported export_format (missing _meta or documents).")


        except (json.JSONDecodeError, IOError) as e:
            raise StorageError(
                "vaultedb failed to load this file — it is not valid JSON and may be corrupted or tampered with.") from e

    def _initialize_meta(self, app_name: Optional[str], salt: Optional[bytes] = None):
        meta = {
            "vault_version": vaultedb_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        if app_name:
            meta["app_name"] = app_name
        if salt:
            meta["salt"] = base64.urlsafe_b64encode(salt).decode("utf-8")
        self.meta = ProtectedMetaDict(meta)

    def _atomic_write(self):
        try:
            file_content = {
                "_meta": dict(self.meta),
                "documents": self.data
            }
            with tempfile.NamedTemporaryFile("w", dir=os.path.dirname(self.path), delete=False) as tf:
                json.dump(file_content, tf, indent=2)
                temp_path = tf.name
            os.replace(temp_path, self.path)
        except Exception as e:
            raise StorageError(f"Atomic write failed: {e}")

    def insert(self, doc: dict) -> str:
        if not isinstance(doc, dict):
            raise InvalidDocumentError("Document must be a dictionary.")
        doc_id = doc.get("_id") or str(uuid.uuid4())
        if doc_id in self.data:
            raise DuplicateIDError(f"Document with _id '{doc_id}' already exists.")
        doc["_id"] = doc_id
        self.data[doc_id] = doc
        self._atomic_write()
        return doc_id

    def get(self, doc_id: str) -> Optional[dict]:
        return self.data.get(doc_id)

    def update(self, doc_id: str, updates: dict) -> bool:
        if not isinstance(updates, dict):
            raise InvalidDocumentError("Update must be a dictionary.")
        if doc_id not in self.data:
            return False
        self.data[doc_id].update(updates)
        self._atomic_write()
        return True

    def delete(self, doc_id: str) -> bool:
        if doc_id in self.data:
            del self.data[doc_id]
            self._atomic_write()
            return True
        return False

    def list(self) -> List[dict]:
        self._load(app_name=None)  # reload to ensure freshness
        return list(self.data.values())
