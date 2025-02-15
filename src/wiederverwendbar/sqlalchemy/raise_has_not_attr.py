from typing import Any


def raise_has_not_attr(obj: Any, name: str) -> bool:
    if not hasattr(obj, name):
        if hasattr(obj, '__class__'):
            obj_name = obj.__class__.__name__
        elif hasattr(obj, '__name__'):
            obj_name = obj.__name__
        else:
            obj_name = str(obj)
        raise AttributeError(f"'{obj_name}' has no attribute '{name}'!")
    return True
