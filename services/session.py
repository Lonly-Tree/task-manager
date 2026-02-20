from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from domain.models import User
from crypto.crypto_service import CryptoService


@dataclass
class SessionContext:
    user: Optional[User] = None
    crypto: Optional[CryptoService] = None
    is_authenticated: bool = False

    def set_session(self, user: User, crypto: CryptoService) -> None:
        if user is None or crypto is None:
            raise ValueError("user and crypto must be provided")
        self.user = user
        self.crypto = crypto
        self.is_authenticated = True

    def clear(self) -> None:
        self.user = None
        self.crypto = None
        self.is_authenticated = False

    def require_auth(self) -> None:
        if not self.is_authenticated or self.user is None or self.crypto is None:
            raise PermissionError("Not authenticated")

    def get_user(self) -> User:
        self.require_auth()
        return self.user

    def get_crypto(self) -> CryptoService:
        self.require_auth()
        return self.crypto