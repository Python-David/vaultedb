import json
import os
import tempfile
from typing import Dict, Optional, List
import uuid
from vaultdb.errors import InvalidDocumentError, DuplicateIDError


class StorageError(Exception):
    pass


class DocumentStorage:
    """
    Handles loading and saving encrypted documents to disk in JSON format.
    Used as the low-level storage engine by VaultDB.

    Responsibilities:
    - Read/write all documents to a single JSON file
    - Assign unique _id to documents if not provided
    - Ensure atomicity during write operations
    - Validate input types
    - Support listing all documents
    - Enforce unique _id per document
    """

    def __init__(self, path: str):
        self.path = path
        self.data: Dict[str, dict] = {}
        self._load()

    def _load(self):
        if not os.path.exists(self.path):
            self.data = {}
            return

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    self.data = {}
                else:
                    self.data = json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            raise StorageError(f"Failed to load storage file: {e}")

    def _atomic_write(self):
        try:
            with tempfile.NamedTemporaryFile("w", dir=os.path.dirname(self.path), delete=False) as tf:
                json.dump(self.data, tf, indent=2)
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
        """Return all stored documents."""
        self._load()  # Ensure latest file data is read
        return list(self.data.values())