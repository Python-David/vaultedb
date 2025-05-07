import os
import sys
from typing import Optional, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vaultdb.storage import DocumentStorage
from vaultdb.crypto import encrypt_document, decrypt_document, CryptoError
from vaultdb.errors import InvalidDocumentError, DuplicateIDError
import uuid


class EncryptedStorage:
    """
    Wraps DocumentStorage to provide transparent encryption/decryption of documents.

    Documents are encrypted before writing to disk and decrypted on read.
    The _id field is stored in plaintext to enable efficient lookup.
    """

    def __init__(self, path: str, key: bytes):
        self.key = key
        self.store = DocumentStorage(path)

    def insert(self, doc: dict) -> str:
        if not isinstance(doc, dict):
            raise InvalidDocumentError("Document must be a dictionary.")
        _id = doc.get("_id") or str(uuid.uuid4())
        doc["_id"] = _id  # ensure internal _id matches external
        try:
            encrypted = encrypt_document(doc, self.key)
            return self.store.insert({"_id": _id, "data": encrypted})
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
            return decrypt_document(raw["data"], self.key)
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
            return self.store.update(doc_id, {"data": encrypted})
        except Exception as e:
            raise CryptoError(f"Update failed: {e}")

    def delete(self, doc_id: str) -> bool:
        return self.store.delete(doc_id)

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
