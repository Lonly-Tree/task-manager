from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.models import TaskNote


class SQLAlchemyNoteRepository:
    def __init__(self, session: Session):
        self._session = session

    def create(self, note: TaskNote) -> TaskNote:
        self._session.add(note)
        self._session.commit()
        self._session.refresh(note)
        return note

    def find_by_id(self, note_id: int) -> TaskNote | None:
        return self._session.get(TaskNote, note_id)

    def find_by_task(self, task_id: int) -> list[TaskNote]:
        stmt = (
            select(TaskNote)
            .where(TaskNote.task_id == task_id)
            .order_by(TaskNote.created_at.asc())
        )
        return list(self._session.execute(stmt).scalars().all())

    def update(self, note: TaskNote) -> TaskNote:
        # note is already attached or merged by caller
        self._session.commit()
        self._session.refresh(note)
        return note

    def delete(self, note_id: int) -> None:
        note = self._session.get(TaskNote, note_id)
        if note is None:
            return
        self._session.delete(note)
        self._session.commit()
