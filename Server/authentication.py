import hashlib
from config import PASSWORD


def verify_password(provided_password: str):
    return provided_password == PASSWORD


def hash_document(content: str):
    """
    Generate SHA-256 hash of document content for duplicate detection.
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass
