from __future__ import annotations
import os
from datetime import datetime
from domain.models import User
from services.session import SessionContext
from crypto.key_manager import KeyManager
from crypto.key_deriver import KeyDeriver
from crypto.crypto_service import CryptoService
from crypto.password_hasher import PasswordHasher


class AuthService:
    def __init__(
        self,
        user_repo,
        session: SessionContext,
        key_manager: KeyManager,
        hasher: PasswordHasher,
    ):
        self._user_repo = user_repo
        self._session = session
        self._key_manager = key_manager
        self._hasher = hasher

    def register(self, username: str, password: str) -> User:
        username = (username or "").strip()
        if not username:
            raise ValueError("Username cannot be empty")
        if not password:
            raise ValueError("Password cannot be empty")

        self._assert_username_available(username)

        password_hash = self._hasher.hash_password(password)
        user_salt = self._generate_salt()

        user = User(
            username=username,
            password_hash=password_hash,
            salt=user_salt,
            created_at=datetime.utcnow(),
        )
        return self._user_repo.create(user)

    def login(self, username: str, password: str) -> SessionContext:
        username = (username or "").strip()
        if not username or not password:
            raise ValueError("Invalid username or password")

        user = self._user_repo.find_by_username(username)
        if user is None:
            raise ValueError("Invalid username or password")

        ok = self._hasher.verify_password(password, user.password_hash)
        if not ok:
            raise ValueError("Invalid username or password")

        master_key = self._key_manager.get_master_key()
        deriver = KeyDeriver(master_key)
        user_key = deriver.derive_user_key(user.salt, user.id)

        crypto = CryptoService(user_key)

        self._session.set_session(user, crypto)
        return self._session

    def logout(self) -> None:
        self._session.clear()

    def get_current_user(self) -> User:
        return self._session.get_user()

    def _generate_salt(self) -> bytes:
        return os.urandom(16)

    def _assert_username_available(self, username: str) -> None:
        existing = self._user_repo.find_by_username(username)
        if existing is not None:
            raise ValueError("Username already exists")