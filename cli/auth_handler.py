from __future__ import annotations

from cli.formatter import OutputFormatter


class AuthCommandHandler:
    def __init__(self, auth_service):
        self._auth = auth_service

    def handle_register(self, args) -> int:
        try:
            self._auth.register(username=args.username, password=args.password)
            print(OutputFormatter.success("User registered"))
            return 0
        except Exception as e:
            print(OutputFormatter.error(str(e)))
            return 1

    def handle_login(self, args) -> int:
        try:
            self._auth.login(username=args.username, password=args.password)
            print(OutputFormatter.success("Logged in"))
            return 0
        except Exception as e:
            print(OutputFormatter.error(str(e)))
            return 1

    def handle_logout(self, args) -> int:
        try:
            self._auth.logout()
            print(OutputFormatter.success("Logged out"))
            return 0
        except Exception as e:
            print(OutputFormatter.error(str(e)))
            return 1