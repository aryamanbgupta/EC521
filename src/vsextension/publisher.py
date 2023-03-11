from typing import AnyStr


class Publisher:
    """Represents a publisher of an extension"""

    def __init__(self, publisher_id: AnyStr, publisher_name: AnyStr):
        self.publisher_id = publisher_id
        self.publisher_name = publisher_name

    def __str__(self):
        return f"Publisher: {self.publisher_name}"
