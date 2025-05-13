import logging
import os
import json
import sys
from datetime import datetime, timezone
from typing import Optional, List, Dict, Callable
import base64

from cryptography.fernet import Fernet, InvalidToken

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vaultedb.errors import CryptoError

logger = logging.getLogger(__name__)


class VaultAuditLog:
    """
    Handles encrypted append-only audit logging for vaultedb operations.

    Each log entry is a base64-encoded, Fernet-encrypted JSON line stored in a `.vaultlog` file.
    This ensures zero-trust observability: auditability without leaking sensitive data.

    Notes:
    - Log file is encrypted using the vault key (no plaintext logs)
    - No key rotation support in MVP (entries use the original vault key)
    - Performance note: `.entries()` loads full log into memory — acceptable for MVP scope
    """

    def __init__(self, log_path: str, key: bytes, on_log_error: Optional[Callable[[Exception], None]] = None):
        """
        Initializes the VaultAuditLog instance.

        Args:
            log_path (str): The file path where the audit log will be stored.
            key (bytes): A Fernet-compatible key used to encrypt/decrypt log entries. Must match the vault key.
            on_log_error (Callable[[Exception], None], optional):
                A custom error handler function that will be called if an exception occurs during logging.
                Useful for integrating with external logging systems or alerts (e.g., Sentry, Datadog).
                If not provided, a fallback logger.warning will be used.

        Notes:
        - The log file is encrypted; contents cannot be read without the same key used for the vault.
        - File permissions will be set to 600 (rw-------) if supported by the OS.
        """
        self.log_path = log_path
        self.fernet = Fernet(key)
        self.on_log_error = on_log_error

        # Set secure permissions if file is being created
        if not os.path.exists(self.log_path):
            with open(self.log_path, "wb") as f:
                pass
            try:
                os.chmod(self.log_path, 0o600)
            except Exception:
                pass  # Don't fail if platform doesn't support chmod

    def log(self, op: str, doc_id: str, meta: Optional[Dict] = None):
        """
        Records an encrypted audit log entry.

        Args:
            op (str): Operation type (e.g., "insert", "get", "update", "delete")
            doc_id (str): Document ID involved in the operation
            meta (dict, optional): Additional metadata (e.g. app label, keys touched)
        """
        meta = meta or {}
        entry = {
            "op": op,
            "_id": doc_id,
            "at": datetime.now(timezone.utc).isoformat(),
            "meta": meta,
        }

        try:
            serialized = json.dumps(entry, ensure_ascii=False).encode("utf-8")
            encrypted = self.fernet.encrypt(serialized)
            with open(self.log_path, "ab") as f:
                f.write(encrypted + b"\n")
        except Exception as e:
            if self.on_log_error:
                self.on_log_error(e)
            else:
                # Default fallback for MVP: log warning
                logger.warning("VaultAuditLog failed to log operation: %s", e)

    def entries(self) -> List[Dict]:
        """
        Decrypts and returns all log entries.

        Returns:
            List[Dict]: List of decrypted audit entries

        Raises:
            CryptoError: If a line cannot be decrypted
        """
        entries = []
        if not os.path.exists(self.log_path):
            return entries

        try:
            with open(self.log_path, "rb") as f:
                for line in f:
                    try:
                        decrypted = self.fernet.decrypt(line.strip())
                        entries.append(json.loads(decrypted.decode("utf-8")))
                    except InvalidToken as e:
                        raise CryptoError("Failed to decrypt audit log entry.") from e
        except Exception as e:
            raise CryptoError("Failed to read audit log.") from e

        return entries

    def tail(self, n: int = 10) -> List[Dict]:
        """
        Returns the last `n` decrypted log entries.

        Args:
            n (int): Number of entries to return

        Returns:
            List[Dict]: Most recent decrypted entries
        """
        return self.entries()[-n:]

    def export_json(self, filepath: str):
        """
        Writes all decrypted audit log entries to a plaintext JSON file.

        Args:
            filepath (str): Path to output file
        """
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.entries(), f, indent=2)
