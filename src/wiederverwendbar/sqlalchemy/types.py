from enum import Enum
from typing import Any

from sqlalchemy import TypeDecorator, Integer, String, Text


class _EnumValue(TypeDecorator):
    """
    Enables passing in a Python enum and storing the enum's *value* in the db.
    The default would have stored the enum's *name* (ie the string).
    """

    # impl = Integer
    cache_ok = True

    def __init__(self, enum_type, *args, **kwargs):
        super(_EnumValue, self).__init__(*args, **kwargs)
        self._enum_type = enum_type

    def process_bind_param(self, value, dialect):
        if isinstance(value, Enum):
            return value.value
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return self._enum_type(value)


class EnumValueStr(_EnumValue):
    impl = Text

class EnumValueInt(_EnumValue):
    impl = Integer


class StringBool(TypeDecorator):
    impl = Integer
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is None:
            return False
        elif value == "0":
            return False
        else:
            return True


class StringList(TypeDecorator):
    impl = String
    cache_ok = True

    def __init__(self, annotation: type, separator: str = ",", empty_is_none: bool = False, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.annotation = annotation
        self.separator = separator
        self.empty_is_none = empty_is_none

    def process_result_value(self, value, dialect):
        value_converted = []
        if value is None:
            if self.empty_is_none:
                value_converted = None
        else:
            split = value.split(self.separator)
            for item in split:
                item_converted = self.annotation(item)
                value_converted.append(item_converted)

        return value_converted
