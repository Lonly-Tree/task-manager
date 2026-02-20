import os, base64
from dotenv import load_dotenv

class KeyManager:
    def __init__(self, master_key: bytes):
        self._validate_key(master_key)
        self._master_key = master_key

    @staticmethod
    def from_env(var_name: str) -> "KeyManager":
        load_dotenv()
        raw = os.getenv(var_name)
        if not raw:
            raise ValueError(f"Missing env var: {var_name}")

        # assume base64
        key = base64.b64decode(raw)
        return KeyManager(key)

    def get_master_key(self) -> bytes:
        return self._master_key

    def _validate_key(self, key: bytes) -> None:
        if not isinstance(key, (bytes, bytearray)):
            raise TypeError("Master key must be bytes")
        if len(key) != 32:
            raise ValueError("Master key must be exactly 32 bytes (AES-256)")
        

