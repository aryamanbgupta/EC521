from typing import AnyStr


class EditorContext:
    def __init__(self, command: AnyStr, title: AnyStr):
        self.command = command
        self.title = title

    def __str__(self):
        return f"{self.title}"
