from typing import Any, Iterable


async def async_for(items: Iterable[Any]) -> Any:
    """Iterate over a iterable asynchronously

    Args:
        items (Iterable[Any]): items to iterate over

    Returns:
        Any: yield items
    """
    for item in items:
        yield item
