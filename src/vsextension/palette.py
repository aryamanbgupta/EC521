from typing import AnyStr


class CommandPalette:
    def __init__(self, command: AnyStr, when: AnyStr):
        self.command = command
        self.when = when

    def __str__(self):
        return f"{self.command}"

    def __eq__(self, other):
        if isinstance(other, CommandPalette):
            return self.command == other.command
        elif isinstance(other, str):
            return self.command == other
        else:
            return False
