from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import os, base64
from dotenv import load_dotenv

class KeyDeriver:
    def __init__(self, master_key:bytes):
        self._validate_key(master_key)
        self._master_key = master_key

    def derive_user_key(self, user_salt: bytes, user_id: int) -> bytes:
        if not isinstance(user_salt, (bytes, bytearray)):
            raise TypeError("user_salt must be bytes")

        if len(user_salt) < 16:
            raise ValueError("user_salt must be at least 16 bytes")

        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("user_id must be a positive integer")

        info = b"taskmanager-user-" + str(user_id).encode()

        return self._hkdf(self._master_key, user_salt, info)

    def _hkdf(self, master_key: bytes, salt: bytes, info: bytes) -> bytes:
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,              # AES-256 → 32 bytes
            salt=salt,
            info=info,
            backend=default_backend()
        )

        return hkdf.derive(master_key)

    def _validate_key(self, key: bytes) -> None:
        if not isinstance(key, (bytes, bytearray)):
            raise TypeError("Master key must be bytes")
        if len(key) != 32:
            raise ValueError("Master key must be exactly 32 bytes (AES-256)")
        
