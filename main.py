#testing the Database!

from repositories.database import SessionLocal, engine
from domain.models import Base, User
from INoteRepository.user_repository import SQLAlchemyUserRepository

Base.metadata.create_all(engine)

with SessionLocal() as session:
    repo = SQLAlchemyUserRepository(session)

    u = User(username="abdo", password_hash="x", salt=b"123")
    repo.create(u)

    found = repo.find_by_username("abdo")
    print(found.id, found.username)