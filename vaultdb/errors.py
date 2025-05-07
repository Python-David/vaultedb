class InvalidDocumentError(Exception):
    pass

class DuplicateIDError(Exception):
    """Raised when a document with the same _id already exists."""
    pass

class CryptoError(Exception):
    pass

class StorageError(Exception):
    pass