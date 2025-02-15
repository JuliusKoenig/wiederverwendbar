from typing import Any

from sqlalchemy import Integer, TypeDecorator, String
from sqlalchemy.dialects.mysql.enumerated import ENUM


class EnumValue(ENUM):
    def _parse_into_values(self, enums, kw):
        values, objects = super()._parse_into_values(enums=enums, kw=kw)
        values: list[str]
        for enum in self.enum_class.__members__.values():
            for i, value in enumerate(values):
                if value == enum.name:
                    # noinspection PyTypeChecker
                    values[i] = enum.value
        return values, objects


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
