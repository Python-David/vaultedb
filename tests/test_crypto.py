import base64
import pytest
from vaultdb.crypto import (
    generate_key,
    generate_salt,
    encrypt_document,
    decrypt_document,
    encrypt_with_salt,
    decrypt_with_salt,
)
from vaultdb.errors import CryptoError


@pytest.fixture
def passphrase():
    return "vaultdb-mvp-passphrase"


@pytest.fixture
def salt():
    return generate_salt()


@pytest.fixture
def key(passphrase, salt):
    return generate_key(passphrase, salt)


@pytest.fixture
def doc():
    return {"_id": "abc123", "name": "Alice", "email": "alice@example.com"}


def test_key_derivation_is_deterministic(passphrase, salt):
    k1 = generate_key(passphrase, salt)
    k2 = generate_key(passphrase, salt)
    assert k1 == k2


def test_encrypt_and_decrypt_roundtrip(doc, key):
    token = encrypt_document(doc, key)
    out = decrypt_document(token, key)
    assert out == doc


def test_encrypt_invalid_type_raises(key):
    with pytest.raises(CryptoError):
        encrypt_document("not-a-dict", key)


def test_decrypt_invalid_token_raises(key):
    with pytest.raises(CryptoError):
        decrypt_document("not-a-real-token", key)


def test_decrypt_with_wrong_key_fails(doc, salt):
    key1 = generate_key("correct-pass", salt)
    key2 = generate_key("wrong-pass", salt)
    token = encrypt_document(doc, key1)
    with pytest.raises(CryptoError):
        decrypt_document(token, key2)


def test_encrypt_with_salt_blob_is_valid_base64(doc, passphrase):
    blob = encrypt_with_salt(doc, passphrase)
    assert "." in blob
    salt_b64, token = blob.split(".", 1)
    # Check both parts are valid base64
    base64.urlsafe_b64decode(salt_b64.encode())
    base64.urlsafe_b64decode(token.encode())  # Fernet tokens are base64 too



def test_decrypt_with_salt_restores_document(doc, passphrase):
    blob = encrypt_with_salt(doc, passphrase)
    result = decrypt_with_salt(blob, passphrase)
    assert result == doc


def test_decrypt_with_salt_fails_on_tampering(passphrase):
    blob = encrypt_with_salt({"msg": "hi"}, passphrase)
    tampered = blob[:-1] + "A"
    with pytest.raises(CryptoError):
        decrypt_with_salt(tampered, passphrase)


def test_generate_key_type_checks():
    with pytest.raises(TypeError):
        generate_key(123, b"salt")
    with pytest.raises(TypeError):
        generate_key("ok", "not-bytes")
