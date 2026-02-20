import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from domain.models import EncryptedField

class CryptoService:
    def __init__(self, user_key: bytes):
        if not isinstance(user_key, (bytes, bytearray)):
            raise TypeError("user_key must be bytes")

        if len(user_key) != 32:
            raise ValueError("user_key must be exactly 32 bytes (AES-256)")

        self._key = bytes(user_key)
        self._aesgcm = AESGCM(self._key)

    def encrypt(self, plaintext: str) -> EncryptedField:
        if plaintext is None:
            plaintext = ""

        nonce = os.urandom(12)
        ciphertext = self._aesgcm.encrypt(
            nonce,
            plaintext.encode("utf-8"),
            None
        )

        blob = nonce + ciphertext
        return EncryptedField(blob=blob)

    def decrypt(self, field: EncryptedField) -> str:
        if field is None or not field.blob:
            return ""

        blob = field.blob
        nonce = blob[:12]
        ciphertext = blob[12:]

        plaintext = self._aesgcm.decrypt(
            nonce,
            ciphertext,
            None
        )

        return plaintext.decode("utf-8")