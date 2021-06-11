import asyncio
from functools import wraps
from typing import Any


def coroutine(f: Any) -> Any:
    """Wrap async function for use in click."""

    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return asyncio.run(f(*args, **kwargs))

    return wrapper
