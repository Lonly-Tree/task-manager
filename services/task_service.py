# services/task_service.py
from __future__ import annotations

from datetime import datetime
from domain.models import Task, EncryptedField
from domain.enums import Priority, TaskStatus
from services.session import SessionContext


class TaskService:
    def __init__(self, task_repo, session: SessionContext):
        self._task_repo = task_repo
        self._session = session

    def create_task(
        self,
        title: str,
        due_date=None,
        priority: Priority = Priority.MEDIUM,
        category: str | None = None,
        description: str | None = None,
    ) -> Task:
        self._session.require_auth()

        user = self._session.get_user()
        crypto = self._session.get_crypto()

        title_enc = crypto.encrypt(title)
        desc_enc = crypto.encrypt(description or "")

        task = Task(
            owner_id=user.id,
            title_blob=title_enc.blob,
            description_blob=desc_enc.blob if description else None,
            status=TaskStatus.PENDING,
            priority=priority,
            due_date=due_date,
            category=category,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        return self._task_repo.create(task)

    def list_tasks(self) -> list[dict]:
        self._session.require_auth()
        user = self._session.get_user()

        tasks = self._task_repo.find_all_by_owner(user.id)
        return [self._decrypt_task(t) for t in tasks]

    def get_task(self, task_id: int) -> dict:
        self._session.require_auth()
        task = self._get_owned_task(task_id)
        return self._decrypt_task(task)

    def edit_task(self, task_id: int, **fields) -> Task:
        """
        Allowed fields:
        - title (str)
        - description (str|None)
        - due_date
        - priority (Priority)
        - category (str|None)
        - status (TaskStatus)  (optional, if you want)
        """
        self._session.require_auth()
        task = self._get_owned_task(task_id)

        crypto = self._session.get_crypto()

        if "title" in fields and fields["title"] is not None:
            task.title_blob = crypto.encrypt(fields["title"]).blob

        if "description" in fields:
            desc = fields["description"]
            if desc is None or desc == "":
                task.description_blob = None
            else:
                task.description_blob = crypto.encrypt(desc).blob

        if "due_date" in fields:
            task.due_date = fields["due_date"]

        if "priority" in fields and fields["priority"] is not None:
            task.priority = fields["priority"]

        if "category" in fields:
            task.category = fields["category"]

        if "status" in fields and fields["status"] is not None:
            task.status = fields["status"]

        task.updated_at = datetime.utcnow()
        return self._task_repo.update(task)

    def delete_task(self, task_id: int) -> None:
        self._session.require_auth()
        task = self._get_owned_task(task_id)
        self._task_repo.delete(task.id)

    def mark_done(self, task_id: int) -> Task:
        self._session.require_auth()
        task = self._get_owned_task(task_id)

        task.status = TaskStatus.COMPLETED
        task.updated_at = datetime.utcnow()
        return self._task_repo.update(task)

    def _get_owned_task(self, task_id: int) -> Task:
        task = self._task_repo.find_by_id(task_id)
        if task is None:
            raise ValueError("Task not found")

        user = self._session.get_user()
        if task.owner_id != user.id:
            raise PermissionError("You do not have access to this task")

        return task

    def _decrypt_task(self, task: Task) -> dict:
        crypto = self._session.get_crypto()

        title = crypto.decrypt(EncryptedField(blob=task.title_blob))
        description = ""
        if task.description_blob:
            description = crypto.decrypt(EncryptedField(blob=task.description_blob))

        status_val = task.status.value if hasattr(task.status, "value") else task.status
        priority_val = task.priority.value if hasattr(task.priority, "value") else task.priority

        return {
            "id": task.id,
            "title": title,
            "description": description,
            "status": status_val,
            "priority": priority_val,
            "due_date": task.due_date,
            "category": task.category,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }