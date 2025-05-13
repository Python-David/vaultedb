"""
vaultedb Crypto Module

Provides transparent encryption and decryption using Fernet.
- Derives keys from passphrase + salt using PBKDF2
- Encrypts/Decrypts vaultedb documents (dicts)
- Includes optional helpers for salt handling and blob packaging
"""

import json
import sys
import os
from typing import Dict, Union

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vaultedb.errors import CryptoError
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64


def generate_key(passphrase: str, salt: bytes, iterations: int = 100_000) -> bytes:
    """
    Derives a 32-byte Fernet key from the given passphrase and salt.
    """
    if not isinstance(passphrase, str) or not isinstance(salt, bytes):
        raise TypeError("Passphrase must be str and salt must be bytes.")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))


def generate_salt(length: int = 16) -> bytes:
    """
    Generates a random salt of the given length (default 16 bytes).
    """
    return os.urandom(length)


def encrypt_document(doc: Dict, key: bytes) -> str:
    """
    Encrypts a Python dictionary and returns a Fernet token as a base64 string.
    """
    if not isinstance(doc, dict):
        raise CryptoError("Document must be a dictionary.")
    try:
        json_data = json.dumps(doc, ensure_ascii=False).encode("utf-8")
        f = Fernet(key)
        return f.encrypt(json_data).decode("utf-8")
    except (TypeError, ValueError) as e:
        raise CryptoError(f"Document is not JSON-serializable: {e}")
    except Exception as e:
        raise CryptoError(f"Encryption failed: {e}")


def decrypt_document(token: Union[str, bytes], key: bytes) -> dict:
    """
    Decrypts a document from a Fernet token using the given key.
    """
    try:
        f = Fernet(key)
        decrypted = f.decrypt(token.encode("utf-8"))
        return json.loads(decrypted.decode("utf-8"))
    except Exception as e:
        raise CryptoError(f"Decryption failed: {e}")


def encrypt_with_salt(doc: Dict, passphrase: str) -> str:
    """
    Encrypts a document with a new salt. Returns a string blob in the export_format:
    base64(salt) + '.' + token

    This avoids issues where raw binary salt might contain delimiter characters.
    """
    try:
        salt = generate_salt()
        key = generate_key(passphrase, salt)
        token = encrypt_document(doc, key)  # already base64 str
        salt_b64 = base64.urlsafe_b64encode(salt).decode("utf-8")
        return f"{salt_b64}.{token}"
    except Exception as e:
        raise CryptoError(f"encrypt_with_salt failed: {e}")


def decrypt_with_salt(blob: str, passphrase: str) -> Dict:
    """
    Decrypts a blob in the export_format: base64(salt) + '.' + token
    using the provided passphrase.
    Returns the original document as a dict.
    """
    try:
        if "." not in blob:
            raise CryptoError("Invalid blob export_format: missing separator.")
        salt_b64, token = blob.split(".", 1)
        salt = base64.urlsafe_b64decode(salt_b64.encode("utf-8"))
        key = generate_key(passphrase, salt)
        return decrypt_document(token, key)
    except Exception as e:
        raise CryptoError(f"decrypt_with_salt failed: {e}")
