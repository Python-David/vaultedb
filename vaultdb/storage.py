import json
import os
import tempfile
from datetime import datetime, timezone
from typing import Dict, Optional, List
import uuid
from vaultdb.errors import InvalidDocumentError, DuplicateIDError, StorageError
from vaultdb.config import VAULTDB_VERSION


class ProtectedMetaDict(dict):
    _protected_keys = {"created_at", "vault_version"}
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
    Handles loading and saving encrypted documents to disk in JSON format.
    Used as the low-level storage engine by VaultDB. Now includes metadata for versioning and app context.

    File schema:
    {
        "_meta": {
            "vault_version": "1.0.0",
            "created_at": "...",
            "app_name": "..."
        },
        "documents": {
            "abc123": {"_id": "abc123", "data": "..."}
        }
    }

    Responsibilities:
    - Read/write all documents to a single JSON file
    - Assign unique _id to documents if not provided
    - Ensure atomicity during write operations
    - Validate input types
    - Support listing all documents
    - Enforce unique _id per document
    """

    def __init__(self, path: str, app_name: Optional[str] = None):
        self.path = path
        self.meta: ProtectedMetaDict = ProtectedMetaDict()
        self.data: Dict[str, dict] = {}
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
                else:
                    raise StorageError("Vault file is not in supported format (missing _meta or documents).")

        except (json.JSONDecodeError, IOError) as e:
            raise StorageError(f"Failed to load storage file: {e}")

    def _initialize_meta(self, app_name: Optional[str]):
        meta = {
            "vault_version": VAULTDB_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        if app_name:
            meta["app_name"] = app_name
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