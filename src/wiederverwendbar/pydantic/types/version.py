from typing import Annotated, Any, Optional

from pydantic_core import core_schema

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue


class VersionType:
    """
    A class representing a version number in the format major.minor.patch.
    """

    def __init__(self,
                 *args,
                 major: Optional[int] = None,
                 minor: Optional[int] = None,
                 patch: Optional[int] = None):
        if len(args) == 1 and isinstance(args[0], str):
            version_str = args[0]
            if version_str.startswith("v"):
                version_str = version_str[1:]
            parts = version_str.split('.')
            if len(parts) != 3:
                raise ValueError(f"Invalid version string: {version_str}")
            major, minor, patch = parts
        elif len(args) == 3:
            major, minor, patch = args
        self._major = None
        self.major = major
        self._minor = None
        self.minor = minor
        self._patch = None
        self.patch = patch

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"

    def __repr__(self):
        return f"{self.__class__.__name__}(major={self.major}, minor={self.minor}, patch={self.patch})"

    @property
    def major(self) -> int:
        """
        The major version number of the version.

        :return: The major version number.
        :rtype: int
        """

        return self._major

    @major.setter
    def major(self, value: int):
        value = int(value)
        if value < 0:
            raise ValueError("Major version must be a non-negative integer")
        self._major = value

    @property
    def minor(self) -> int:
        """
        The minor version number of the version.

        :return: The minor version number.
        :rtype: int
        """

        return self._minor

    @minor.setter
    def minor(self, value: int):
        value = int(value)
        if value < 0:
            raise ValueError("Minor version must be a non-negative integer")
        self._minor = value

    @property
    def patch(self) -> int:
        """
        The patch version number of the version.

        :return: The patch version number.
        :rtype: int
        """

        return self._patch

    @patch.setter
    def patch(self, value: int):
        value = int(value)
        if value < 0:
            raise ValueError("Patch version must be a non-negative integer")
        self._patch = value


class _VersionTypePydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(cls,
                                     _source_type: Any,
                                     _handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        from_str_schema = core_schema.chain_schema([core_schema.str_schema(),
                                                    core_schema.no_info_plain_validator_function(lambda value: value if isinstance(value, VersionType) else VersionType(value))])

        return core_schema.json_or_python_schema(json_schema=from_str_schema,
                                                 python_schema=core_schema.union_schema([
                                                     core_schema.is_instance_schema(VersionType),
                                                     from_str_schema]),
                                                 serialization=core_schema.plain_serializer_function_ser_schema(lambda instance: str(instance)))

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        h = handler(core_schema.str_schema())
        h["example"] = str(VersionType("0.1.0"))
        return h



Version = Annotated[VersionType, _VersionTypePydanticAnnotation]
