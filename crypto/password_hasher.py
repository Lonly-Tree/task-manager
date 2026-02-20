from argon2 import PasswordHasher as _PH
from argon2.exceptions import VerifyMismatchError

class PasswordHasher:
    def __init__(self):
        self._ph = _PH()
        
    def hash_password(self, plaintext: str) -> str:
        if not plaintext:
            raise ValueError("Password cannot be empty")
        return self._ph.hash(plaintext)

    def verify_password(self, plaintext: str, stored_hash: str) -> bool:
        try:
            return self._ph.verify(stored_hash, plaintext)
        except VerifyMismatchError:
            return False
        

