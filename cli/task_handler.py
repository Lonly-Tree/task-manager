# cli/task_handler.py
from __future__ import annotations

from cli.formatter import OutputFormatter
from domain.enums import Priority


class TaskCommandHandler:
    def __init__(self, task_service):
        self._tasks = task_service

    def handle_add(self, args) -> int:
        try:
            priority = Priority(args.priority.upper())

            self._tasks.create_task(
                title=args.title,
                description=args.description,
                priority=priority,
                category=args.category,
                due_date=args.due,
            )

            print(OutputFormatter.success("Task created"))
            return 0

        except Exception as e:
            print(OutputFormatter.error(str(e)))
            return 1

    def handle_list(self, args) -> int:
        try:
            tasks = self._tasks.list_tasks()
            print(OutputFormatter.format_tasks(tasks))
            return 0

        except Exception as e:
            print(OutputFormatter.error(str(e)))
            return 1

    def handle_show(self, args) -> int:
        try:
            task = self._tasks.get_task(args.id)
            print(OutputFormatter.format_task_detail(task))
            return 0

        except Exception as e:
            print(OutputFormatter.error(str(e)))
            return 1

    def handle_edit(self, args) -> int:
        try:
            fields = {}

            if args.title is not None:
                fields["title"] = args.title

            if args.description is not None:
                fields["description"] = args.description

            if args.priority is not None:
                fields["priority"] = Priority(args.priority.upper())

            if args.category is not None:
                fields["category"] = args.category

            if args.due is not None:
                fields["due_date"] = args.due

            self._tasks.edit_task(args.id, **fields)

            print(OutputFormatter.success("Task updated"))
            return 0

        except Exception as e:
            print(OutputFormatter.error(str(e)))
            return 1

    def handle_done(self, args) -> int:
        try:
            self._tasks.mark_done(args.id)
            print(OutputFormatter.success("Task marked completed"))
            return 0

        except Exception as e:
            print(OutputFormatter.error(str(e)))
            return 1

    def handle_delete(self, args) -> int:
        try:
            self._tasks.delete_task(args.id)
            print(OutputFormatter.success("Task deleted"))
            return 0

        except Exception as e:
            print(OutputFormatter.error(str(e)))
            return 1