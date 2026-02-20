# cli/router.py
from __future__ import annotations

import argparse


class CLIRouter:
    def __init__(self, auth_handler, task_handler, note_handler, session):
        self._auth = auth_handler
        self._tasks = task_handler
        self._notes = note_handler
        self._session = session

    def run(self, argv: list[str]) -> int:
        parser = self._build_parser()
        args = parser.parse_args(argv)
        return self._dispatch(args)

    def _build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="taskmgr")
        sub = parser.add_subparsers(dest="cmd", required=True)

        # -------------------------
        # AUTH
        # -------------------------
        auth = sub.add_parser("auth", help="Authentication commands")
        auth_sub = auth.add_subparsers(dest="auth_cmd", required=True)

        reg = auth_sub.add_parser("register", help="Register a new user")
        reg.add_argument("username")
        reg.add_argument("password")

        login = auth_sub.add_parser("login", help="Login")
        login.add_argument("username")
        login.add_argument("password")

        auth_sub.add_parser("logout", help="Logout")

        task = sub.add_parser("task", help="Task commands")
        task_sub = task.add_subparsers(dest="task_cmd", required=True)

        t_add = task_sub.add_parser("add", help="Add a task")
        t_add.add_argument("title")
        t_add.add_argument("--description", default=None)
        t_add.add_argument("--priority", default="MEDIUM", choices=["LOW", "MEDIUM", "HIGH"])
        t_add.add_argument("--category", default=None)
        t_add.add_argument("--due", default=None)

        task_sub.add_parser("list", help="List tasks")

        t_show = task_sub.add_parser("show", help="Show a task")
        t_show.add_argument("id", type=int)

        t_edit = task_sub.add_parser("edit", help="Edit a task")
        t_edit.add_argument("id", type=int)
        t_edit.add_argument("--title", default=None)
        t_edit.add_argument("--description", default=None)
        t_edit.add_argument("--priority", choices=["LOW", "MEDIUM", "HIGH"], default=None)
        t_edit.add_argument("--category", default=None)
        t_edit.add_argument("--due", default=None)

        t_done = task_sub.add_parser("done", help="Mark task as completed")
        t_done.add_argument("id", type=int)

        t_del = task_sub.add_parser("delete", help="Delete a task")
        t_del.add_argument("id", type=int)

        note = sub.add_parser("note", help="Note commands")
        note_sub = note.add_subparsers(dest="note_cmd", required=True)

        n_add = note_sub.add_parser("add", help="Add a note to a task")
        n_add.add_argument("task_id", type=int)
        n_add.add_argument("content")

        n_list = note_sub.add_parser("list", help="List notes for a task")
        n_list.add_argument("task_id", type=int)

        n_edit = note_sub.add_parser("edit", help="Edit a note")
        n_edit.add_argument("note_id", type=int)
        n_edit.add_argument("content")

        n_del = note_sub.add_parser("delete", help="Delete a note")
        n_del.add_argument("note_id", type=int)

        return parser


    def _dispatch(self, args) -> int:
        if args.cmd == "auth":
            return self._dispatch_auth(args)

        if args.cmd == "task":
            self._require_auth()
            return self._dispatch_task(args)

        if args.cmd == "note":
            self._require_auth()
            return self._dispatch_note(args)

        raise ValueError("Unknown command")

    def _dispatch_auth(self, args) -> int:
        if args.auth_cmd == "register":
            return self._auth.handle_register(args)
        if args.auth_cmd == "login":
            return self._auth.handle_login(args)
        if args.auth_cmd == "logout":
            return self._auth.handle_logout(args)
        raise ValueError("Unknown auth command")

    def _dispatch_task(self, args) -> int:
        if args.task_cmd == "add":
            return self._tasks.handle_add(args)
        if args.task_cmd == "list":
            return self._tasks.handle_list(args)
        if args.task_cmd == "show":
            return self._tasks.handle_show(args)
        if args.task_cmd == "edit":
            return self._tasks.handle_edit(args)
        if args.task_cmd == "done":
            return self._tasks.handle_done(args)
        if args.task_cmd == "delete":
            return self._tasks.handle_delete(args)
        raise ValueError("Unknown task command")

    def _dispatch_note(self, args) -> int:
        if args.note_cmd == "add":
            return self._notes.handle_add(args)
        if args.note_cmd == "list":
            return self._notes.handle_list(args)
        if args.note_cmd == "edit":
            return self._notes.handle_edit(args)
        if args.note_cmd == "delete":
            return self._notes.handle_delete(args)
        raise ValueError("Unknown note command")

    def _require_auth(self) -> None:
        if not self._session.is_authenticated:
            raise PermissionError("You must login first. Use: taskmgr auth login <username> <password>")