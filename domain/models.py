from sqlalchemy import ForeignKey, Integer, LargeBinary, String, DateTime
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column,relationship
from repositories.database import Base
from enums import TaskStatus, Priority

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    salt: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow) # type: ignore

    tasks: Mapped[list["Task"]] = relationship(back_populates="owner")


class Task(Base):

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    title_blob: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    description_blob: Mapped[bytes | None] = mapped_column(LargeBinary)

    status: Mapped[TaskStatus] = mapped_column(String, default="PENDING")
    priority: Mapped[Priority] = mapped_column(String, default="MEDIUM")

    due_date: Mapped[str | None] = mapped_column(String)
    category: Mapped[str | None] = mapped_column(String)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow) # type: ignore
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow) # type: ignore

    owner: Mapped["User"] = relationship(back_populates="tasks")
    notes: Mapped[list["TaskNote"]] = relationship(
        back_populates="task",
        cascade="all, delete"
    )


class TaskNote(Base):
    __tablename__ = "task_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))

    content_blob: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow) # type: ignore
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow) # type: ignore

    task: Mapped["Task"] = relationship(back_populates="notes")