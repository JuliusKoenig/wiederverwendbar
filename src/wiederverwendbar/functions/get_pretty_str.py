from enum import Enum


def get_pretty_str(value):
    if type(value) is str:
        return f"'{value}'"
    elif isinstance(value, Enum):
        return get_pretty_str(value.value)
    return f"{value}"
