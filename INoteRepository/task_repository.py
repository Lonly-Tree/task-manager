from __future__ import annotations

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.models import Task


class SQLAlchemyTaskRepository:
    def __init__(self, session: Session):
        self._session = session

    def create(self, task: Task) -> Task:
        self._session.add(task)
        self._session.commit()
        self._session.refresh(task)
        return task

    def find_by_id(self, task_id: int) -> Task | None:
        return self._session.get(Task, task_id)

    def find_all_by_owner(self, owner_id: int) -> list[Task]:
        stmt = (
            select(Task)
            .where(Task.owner_id == owner_id)
            .order_by(Task.created_at.desc())
        )
        return list(self._session.execute(stmt).scalars().all())

    def update(self, task: Task) -> Task:
        # assumes task is already loaded/attached to session
        task.updated_at = datetime.utcnow()
        self._session.commit()
        self._session.refresh(task)
        return task

    def delete(self, task_id: int) -> None:
        task = self._session.get(Task, task_id)
        if task is None:
            return
        self._session.delete(task)
        self._session.commit()

    def mark_completed(self, task_id: int) -> None:
        task = self._session.get(Task, task_id)
        if task is None:
            return
        task.status = "COMPLETED"
        task.updated_at = datetime.utcnow()
        self._session.commit()
