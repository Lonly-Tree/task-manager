from __future__ import annotations

from datetime import datetime
from domain.models import TaskNote, EncryptedField, Task
from services.session import SessionContext


class NoteService:
    def __init__(self, note_repo, task_repo, session: SessionContext):
        self._note_repo = note_repo
        self._task_repo = task_repo
        self._session = session

    def add_note(self, task_id: int, content: str) -> TaskNote:
        self._session.require_auth()
        self._assert_task_accessible(task_id)

        crypto = self._session.get_crypto()
        encrypted = crypto.encrypt(content)

        note = TaskNote(
            task_id=task_id,
            content_blob=encrypted.blob,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        return self._note_repo.create(note)

    def list_notes(self, task_id: int) -> list[dict]:
        self._session.require_auth()
        self._assert_task_accessible(task_id)

        notes = self._note_repo.find_by_task(task_id)
        return [self._decrypt_note(n) for n in notes]

    def edit_note(self, note_id: int, content: str) -> TaskNote:
        self._session.require_auth()

        note = self._note_repo.find_by_id(note_id)
        if note is None:
            raise ValueError("Note not found")

        self._assert_task_accessible(note.task_id)

        crypto = self._session.get_crypto()
        encrypted = crypto.encrypt(content)

        note.content_blob = encrypted.blob
        note.updated_at = datetime.utcnow()

        return self._note_repo.update(note)

    def delete_note(self, note_id: int) -> None:
        self._session.require_auth()

        note = self._note_repo.find_by_id(note_id)
        if note is None:
            return

        self._assert_task_accessible(note.task_id)
        self._note_repo.delete(note_id)

    def _assert_task_accessible(self, task_id: int) -> Task:
        task = self._task_repo.find_by_id(task_id)
        if task is None:
            raise ValueError("Task not found")

        current_user = self._session.get_user()
        if task.owner_id != current_user.id:
            raise PermissionError("You do not have access to this task")

        return task

    def _decrypt_note(self, note: TaskNote) -> dict:
        crypto = self._session.get_crypto()
        plaintext = crypto.decrypt(EncryptedField(blob=note.content_blob))

        return {
            "id": note.id,
            "task_id": note.task_id,
            "content": plaintext,
            "created_at": note.created_at,
            "updated_at": note.updated_at,
        }