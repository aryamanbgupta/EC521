from typing import AnyStr, Dict


class Command:
    def __init__(self, command: AnyStr, title: AnyStr, category: AnyStr = None):
        self.command = command
        self.title = title
        self.category = category
        self.all_type_commands = {"commandPalette": [], "keyBinding": [], "editorContext": [], "editorTitleContext": []}

    def __str__(self):
        if self.category is None or self.category == "":
            return f"{self.title}"
        return f"{self.category}: {self.title}"

    def __eq__(self, other):
        if isinstance(other, Command):
            return self.command == other.command
        elif isinstance(other, str):
            return self.command == other
        return False

    def __hash__(self):
        return hash(self.command)

    @classmethod
    def from_json(cls, data: Dict[str, AnyStr]):
        return cls(data.get("command"), data.get("title"), data.get("category", None))
