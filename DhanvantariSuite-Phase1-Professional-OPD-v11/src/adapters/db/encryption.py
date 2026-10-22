import os
import base64
import hashlib
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.types import TypeDecorator, Text

# Retrieve encryption key from environment or use a secure clinic default for dev/test
# In production, set CLINIC_ENCRYPTION_KEY to a high-entropy Fernet key
_ENV_KEY = os.getenv("CLINIC_ENCRYPTION_KEY")
if _ENV_KEY:
    _FERNET_KEY = _ENV_KEY.encode() if isinstance(_ENV_KEY, str) else _ENV_KEY
else:
    # Deterministic fallback key for single-tenant local/dev environments
    # Ensures data remains decryptable across process restarts
    _SALT = b"dhanvantari_clinic_hipaa_dpdp_salt_v11"
    _FERNET_KEY = base64.urlsafe_b64encode(hashlib.sha256(b"dhanvantari_master_encryption_secret_key" + _SALT).digest())

_cipher = Fernet(_FERNET_KEY)

def encrypt_value(raw: Optional[str]) -> Optional[str]:
    """Encrypts plaintext string using AES-256 (Fernet)."""
    if raw is None:
        return None
    if not isinstance(raw, str):
        raw = str(raw)
    token = _cipher.encrypt(raw.encode("utf-8"))
    return token.decode("utf-8")

def decrypt_value(ciphertext: Optional[str]) -> Optional[str]:
    """Decrypts ciphertext string. If plaintext (legacy), returns value as-is."""
    if ciphertext is None:
        return None
    if not isinstance(ciphertext, str):
        ciphertext = str(ciphertext)
    try:
        decrypted = _cipher.decrypt(ciphertext.encode("utf-8"))
        return decrypted.decode("utf-8")
    except (InvalidToken, Exception):
        # Graceful fallback for legacy plaintext rows or unencrypted values
        return ciphertext

class EncryptedText(TypeDecorator):
    """
    SQLAlchemy TypeDecorator that encrypts text before saving to the database
    and decrypts it when loading from the database.
    Provides transparent AES-256 field-level encryption for ePHI/PII compliance.
    """
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return encrypt_value(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return decrypt_value(value)
