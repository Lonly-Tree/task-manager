from __future__ import annotations
import os
from dotenv import load_dotenv
from repositories import Base, engine, SessionLocal
from INoteRepository import SQLAlchemyUserRepository, SQLAlchemyTaskRepository, SQLAlchemyNoteRepository
from crypto import KeyManager, PasswordHasher
from services import SessionContext, NoteService, TaskService, AuthService
from getpass import getpass
from domain.enums import Priority
from cli.agent_commands import handle_slash

load_dotenv()


def build_app_menu_mode():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    user_repo = SQLAlchemyUserRepository(db)
    task_repo = SQLAlchemyTaskRepository(db)
    note_repo = SQLAlchemyNoteRepository(db)

    session_ctx = SessionContext()

    key_manager = KeyManager.from_env("TASKMGR_MASTER_KEY")
    hasher = PasswordHasher()

    auth_service = AuthService(
        user_repo=user_repo,
        session=session_ctx,
        key_manager=key_manager,
        hasher=hasher,
    )

    task_service = TaskService(
        task_repo=task_repo,
        session=session_ctx,
    )

    note_service = NoteService(
        note_repo=note_repo,
        task_repo=task_repo,
        session=session_ctx,
    )

    return db, auth_service, task_service, note_service, session_ctx


def input_nonempty(prompt: str) -> str:
    while True:
        v = input(prompt).strip()
        if v:
            return v
        print("Please enter a value.")


def auth_menu(auth_service, session_ctx) -> None:
    while not session_ctx.is_authenticated:
        print("\n=== AUTH ===")
        print("1) Create account")
        print("2) Login")
        print("0) Exit")

        choice = input("Choose: ").strip()

        if choice == "1":
            username = input_nonempty("Username: ")
            password = getpass("Password: ")
            try:
                auth_service.register(username, password)
                print("[OK] Account created. Now login.")
            except Exception as e:
                print(f"[ERROR] {e}")

        elif choice == "2":
            username = input_nonempty("Username: ")
            password = getpass("Password: ")
            try:
                auth_service.login(username, password)
                print("[OK] Logged in.")
            except Exception as e:
                print(f"[ERROR] {e}")

        elif choice == "0":
            raise SystemExit(0)
        else:
            print("Invalid choice.")


def main_menu(auth_service, task_service, note_service, session_ctx, graph_cache) -> None:
    while session_ctx.is_authenticated:
        print("\n=== TASK MANAGER ===")
        print("1) Show tasks")
        print("2) Add task")
        print("3) Mark task done")
        print("4) Delete task")
        print("5) Logout")
        print("0) Exit")
        print("Or type /... for AI mode")

        choice = input("Choose: ").strip()

        # AI mode
        if choice.startswith("/"):
            reply = handle_slash(
                raw_line=choice,
                task_service=task_service,
                auth_service=auth_service,
                session_ctx=session_ctx,
                note_service=note_service,
                graph_cache=graph_cache,
            )
            print(reply)
            continue

        if choice == "1":
            try:
                tasks = task_service.list_tasks()
                if not tasks:
                    print("No tasks.")
                else:
                    print(f"{'ID':>3} | {'STATUS':<10} | {'PRIORITY':<7} | TITLE")
                    print("-" * 60)
                    for t in tasks:
                        print(f"{t['id']:>3} | {t['status']:<10} | {t['priority']:<7} | {t['title']}")
            except Exception as e:
                print(f"[ERROR] {e}")

        elif choice == "2":
            title = input_nonempty("Task name: ")
            desc = input("Description (optional): ").strip() or None
            pr = input("Priority LOW/MEDIUM/HIGH (default MEDIUM): ").strip().upper()

            try:
                priority = Priority(pr) if pr else Priority.MEDIUM
            except Exception:
                priority = Priority.MEDIUM

            try:
                task_service.create_task(
                    title=title,
                    description=desc,
                    priority=priority,
                    category=None,
                    due_date=None,
                )
                print("[OK] Task added.")
            except Exception as e:
                print(f"[ERROR] {e}")

        elif choice == "3":
            try:
                task_id = int(input_nonempty("Task ID: "))
                task_service.mark_done(task_id)
                print("[OK] Task marked done.")
            except Exception as e:
                print(f"[ERROR] {e}")

        elif choice == "4":
            try:
                task_id = int(input_nonempty("Task ID: "))
                task_service.delete_task(task_id)
                print("[OK] Task deleted.")
            except Exception as e:
                print(f"[ERROR] {e}")

        elif choice == "5":
            uid = getattr(session_ctx.user, "id", None)
            auth_service.logout()
            print("[OK] Logged out.")

            if uid:
                graph_cache.get("histories", {}).pop(f"user:{uid}", None)

            return

        elif choice == "0":
            raise SystemExit(0)

        else:
            print("Invalid choice.")


def run_app():
    db, auth_service, task_service, note_service, session_ctx = build_app_menu_mode()

    graph_cache = {
        "model": os.getenv("GROQ_MODEL_AI") or "llama-3.3-70b-versatile",
        "histories": {},
    }

    try:
        while True:
            auth_menu(auth_service, session_ctx)

            user_id = getattr(session_ctx.user, "id", None)
            if user_id:
                graph_cache["histories"][f"user:{user_id}"] = []

            main_menu(
                auth_service,
                task_service,
                note_service,
                session_ctx,
                graph_cache,
            )
    finally:
        db.close()