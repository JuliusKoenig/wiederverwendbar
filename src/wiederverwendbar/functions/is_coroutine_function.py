import asyncio
import functools

from typing import Any


def is_coroutine_function(obj: Any) -> bool:
    """
    Check if the object is a coroutine function.

    This function is needed because functools.partial is not a coroutine function, but its func attribute is.

    :param obj: The object to check.
    :return: True if the object is a coroutine function, False otherwise.
    """

    while isinstance(obj, functools.partial):
        obj = obj.func
    return asyncio.iscoroutinefunction(obj)
