from typing import AnyStr
import platform


class KeyBinding:
    os_name = platform.system()

    def __init__(self, command: AnyStr, key: AnyStr, when: AnyStr, mac=None):
        self.command = command
        self.key = key
        self.when = when
        self.mac = mac

    def __str__(self):
        """Return the key binding
        check if mac else return key"""
        if self.os_name == "Darwin":
            return f"{self.mac}"
        else:
            return f"{self.key}"
