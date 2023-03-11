from typing import AnyStr


class Version:
    """Represents a version of an extension"""

    VERSION = "version"
    LAST_UPDATED = "lastUpdated"

    def __init__(self, version: AnyStr, last_updated: AnyStr):
        self.version = version
        self.last_updated = last_updated

    def __str__(self):
        return f"Version: {self.version}"
