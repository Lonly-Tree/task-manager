# cli/note_handler.py
from __future__ import annotations

from .formatter import OutputFormatter


class NoteCommandHandler:
    def __init__(self, note_service):
        self._notes = note_service

    def handle_add(self, args) -> int:
        try:
            self._notes.add_note(task_id=args.task_id, content=args.content)
            print(OutputFormatter.success("Note added"))
            return 0
        except Exception as e:
            print(OutputFormatter.error(str(e)))
            return 1

    def handle_list(self, args) -> int:
        try:
            notes = self._notes.list_notes(task_id=args.task_id)
            print(OutputFormatter.format_notes(notes))
            return 0
        except Exception as e:
            print(OutputFormatter.error(str(e)))
            return 1

    def handle_edit(self, args) -> int:
        try:
            self._notes.edit_note(note_id=args.note_id, content=args.content)
            print(OutputFormatter.success("Note updated"))
            return 0
        except Exception as e:
            print(OutputFormatter.error(str(e)))
            return 1

    def handle_delete(self, args) -> int:
        try:
            self._notes.delete_note(note_id=args.note_id)
            print(OutputFormatter.success("Note deleted"))
            return 0
        except Exception as e:
            print(OutputFormatter.error(str(e)))
            return 1