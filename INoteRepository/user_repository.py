from sqlalchemy import select
from sqlalchemy.orm import Session
from domain.models import User

class SQLAlchemyUserRepository:
    def __init__(self, session: Session):
        self._session = session

    def create(self, user: User) -> User:
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return user

    def find_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return self._session.execute(stmt).scalar_one_or_none()

    def find_by_id(self, user_id: int) -> User | None:
        return self._session.get(User, user_id)

    def update_salt(self, user_id: int, salt: bytes) -> None:
        user = self._session.get(User, user_id)
        if not user:
            return
        user.salt = salt
        self._session.commit()