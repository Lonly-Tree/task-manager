from __future__ import annotations
from repositories import Base, engine, SessionLocal
from INoteRepository import SQLAlchemyUserRepository, SQLAlchemyTaskRepository,SQLAlchemyNoteRepository
from crypto import KeyManager, PasswordHasher
from services import SessionContext, NoteService, TaskService, AuthService
from getpass import getpass

def build_app_menu_mode():
    
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # 3) Repositories
    user_repo = SQLAlchemyUserRepository(db)
    task_repo = SQLAlchemyTaskRepository(db)
    note_repo = SQLAlchemyNoteRepository(db)

    # 4) Session (in-memory, stays until you logout or exit app)
    session_ctx = SessionContext()

    # 5) Crypto utilities
    key_manager = KeyManager.from_env("TASKMGR_MASTER_KEY")
    hasher = PasswordHasher()

    # 6) Services
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

    # return everything main needs
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


def main_menu(auth_service, task_service, note_service, session_ctx) -> None:
    while True:
        print("\n=== TASK MANAGER ===")
        print("1) Show tasks")
        print("2) Add task")
        print("3) Mark task done")
        print("4) Delete task")
        print("5) Logout")
        print("0) Exit")

        choice = input("Choose: ").strip()

        if choice == "1":
            try:
                tasks = task_service.list_tasks()
                if not tasks:
                    print("No tasks.")
                else:
                    for t in tasks:
                        print(f"{t['id']:>3} | {t['status']:<9} | {t['priority']:<6} | {t['title']}")
            except Exception as e:
                print(f"[ERROR] {e}")

        elif choice == "2":
            title = input_nonempty("Task name: ")
            desc = input("Note/Description (optional): ").strip() or None

            # priority optional
            pr = input("Priority LOW/MEDIUM/HIGH (default MEDIUM): ").strip().upper() or "MEDIUM"
            try:
                from domain.enums import Priority
                priority = Priority(pr)
            except Exception:
                print("[ERROR] Invalid priority. Using MEDIUM.")
                from domain.enums import Priority
                priority = Priority.MEDIUM

            try:
                task_service.create_task(title=title, description=desc, priority=priority)
                print("[OK] Task added.")
            except Exception as e:
                print(f"[ERROR] {e}")

        elif choice == "3":
            task_id_str = input_nonempty("Task ID to mark done: ")
            try:
                task_id = int(task_id_str)
                task_service.mark_done(task_id)
                print("[OK] Task marked done.")
            except Exception as e:
                print(f"[ERROR] {e}")

        elif choice == "4":
            task_id_str = input_nonempty("Task ID to delete: ")
            try:
                task_id = int(task_id_str)
                task_service.delete_task(task_id)
                print("[OK] Task deleted.")
            except Exception as e:
                print(f"[ERROR] {e}")

        elif choice == "5":
            auth_service.logout()
            print("[OK] Logged out.")
            return  # return to auth_menu

        elif choice == "0":
            raise SystemExit(0)

        else:
            print("Invalid choice.")


def run_app():
    db, auth_service, task_service, note_service, session_ctx = build_app_menu_mode()
    try:
        while True:
            auth_menu(auth_service, session_ctx)
            main_menu(auth_service=auth_service, task_service=task_service, note_service=note_service, session_ctx=session_ctx)
    finally:
        db.close()

if __name__ == "__main__":
    run_app()