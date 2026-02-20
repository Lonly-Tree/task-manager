from datetime import datetime
from typing import Any


class OutputFormatter:
    @staticmethod
    def success(message: str) -> str:
        return f"[OK] {message}"

    @staticmethod
    def error(message: str) -> str:
        return f"[ERROR] {message}"

    @staticmethod
    def info(message: str) -> str:
        return f"[INFO] {message}"


    @staticmethod
    def format_tasks(tasks: list[dict[str, Any]]) -> str:
        if not tasks:
            return "No tasks found."

        lines = []
        header = f"{'ID':>3} | {'STATUS':<9} | {'PRIORITY':<6} | {'TITLE'}"
        separator = "-" * len(header)

        lines.append(header)
        lines.append(separator)

        for t in tasks:
            lines.append(
                f"{t['id']:>3} | "
                f"{t['status']:<9} | "
                f"{t['priority']:<6} | "
                f"{t['title']}"
            )

        return "\n".join(lines)

    @staticmethod
    def format_task_detail(task: dict[str, Any]) -> str:
        lines = [
            f"ID        : {task['id']}",
            f"Title     : {task['title']}",
            f"Status    : {task['status']}",
            f"Priority  : {task['priority']}",
            f"Category  : {task.get('category') or '-'}",
            f"Due Date  : {OutputFormatter._format_datetime(task.get('due_date'))}",
            f"Created   : {OutputFormatter._format_datetime(task.get('created_at'))}",
            f"Updated   : {OutputFormatter._format_datetime(task.get('updated_at'))}",
            "",
            "Description:",
            task.get("description") or "-"
        ]

        return "\n".join(lines)

    @staticmethod
    def format_notes(notes: list[dict[str, Any]]) -> str:
        if not notes:
            return "No notes found."

        lines = []
        header = f"{'ID':>3} | {'CONTENT'}"
        separator = "-" * len(header)

        lines.append(header)
        lines.append(separator)

        for n in notes:
            lines.append(
                f"{n['id']:>3} | {n['content']}"
            )

        return "\n".join(lines)

    @staticmethod
    def _format_datetime(value):
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M")
        return value or "-"


