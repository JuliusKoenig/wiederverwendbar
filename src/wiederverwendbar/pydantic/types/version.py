from typing import Any, Literal

from pydantic_core import core_schema

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue

PRERELEASE_TYPES = str | Literal["alpha", "beta", "release_candidate"]
PRERELEASE_TYPE_MAPPING = {
    "alpha": "a",
    "beta": "b",
    "release_candidate": "rc"
}
PRERELEASE_TYPE_WEIGHT_MAPPING = {
    "alpha": -1000,
    "beta": -100,
    "release_candidate": -10
}


class Version:
    """
    A class representing a version number in the format major.minor.patch.
    """

    def __init__(self,
                 *args,
                 major: int | str | None = None,
                 minor: int | str | None = None,
                 patch: int | str | None = None,
                 prerelease_type: PRERELEASE_TYPES | None = None,
                 prerelease_number: int | str | None = None):

        # Handle string input
        if len(args) == 1 and isinstance(args[0], str):
            version_str = args[0]
            if version_str.startswith("v"):
                version_str = version_str[1:]
            parts = version_str.split('.')
            if len(parts) != 3:
                raise ValueError(f"Invalid version string: {version_str}")
            major, minor, patch = parts
            # Handle prerelease in patch
            prerelease_index = None
            for i, char in enumerate(patch):
                if char.isalpha():
                    if prerelease_type is None:
                        prerelease_index = i
                        break
            # get prerelease type and number if present
            if prerelease_index is not None:
                if prerelease_type is not None:
                    raise ValueError("Cannot provide prerelease_type when it is already in the version string")
                if prerelease_number is not None:
                    raise ValueError("Cannot provide prerelease_number when it is already in the version string")
                prerelease_part = patch[prerelease_index:]
                patch = patch[:prerelease_index]
                for key, value in PRERELEASE_TYPE_MAPPING.items():
                    if prerelease_part.startswith(value):
                        prerelease_type = key
                        prerelease_number = prerelease_part[len(value):]
                        break
                else:
                    raise ValueError(f"Invalid prerelease type in version string: {version_str}")

        # Handle arguments
        elif len(args) == 3:
            major, minor, patch = args
        elif len(args) == 5:
            major, minor, patch, prerelease_type, prerelease_number = args

        else:
            if major is None or minor is None or patch is None:
                raise ValueError("Either provide a version string or all of major, minor, and patch as integers")

        self._major = None
        self.major = major
        self._minor = None
        self.minor = minor
        self._patch = None
        self.patch = patch
        self._prerelease_type = None
        self.prerelease_type = prerelease_type
        self._prerelease_number = None
        self.prerelease_number = prerelease_number

    def __str__(self):
        s = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease_type is not None:
            s += PRERELEASE_TYPE_MAPPING[self.prerelease_type]
            s += str(self.prerelease_number)
        return s

    def __repr__(self):
        r = f"{self.__class__.__name__}(major={self.major}, minor={self.minor}, patch={self.patch}"
        if self.prerelease_type is not None:
            r += f", prerelease_type='{self.prerelease_type}', prerelease_number={self.prerelease_number}"
        r += ")"
        return r

    def __int__(self):
        """
        Convert the version to an integer representation.

        :return: The integer representation of the version.
        :rtype: int
        """

        value = self.major * 1_000_000 + self.minor * 1_000 + self.patch
        if self.prerelease_type is not None:
            value += self.prerelease_number + PRERELEASE_TYPE_WEIGHT_MAPPING[self.prerelease_type]
        return value

    def __eq__(self, other):
        if isinstance(other, Version):
            return int(self) == int(other)
        else:
            return self == other

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if isinstance(other, Version):
            return int(self) < int(other)
        else:
            return int(self) < other

    def __le__(self, other):
        if isinstance(other, Version):
            return int(self) <= int(other)
        else:
            return int(self) <= other

    def __gt__(self, other):
        if isinstance(other, Version):
            return int(self) > int(other)
        else:
            return int(self) > other

    def __ge__(self, other):
        if isinstance(other, Version):
            return int(self) >= int(other)
        else:
            return int(self) >= other

    @classmethod
    def __get_pydantic_core_schema__(cls,
                                     _source_type: Any,
                                     _handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        from_str_schema = core_schema.chain_schema([core_schema.str_schema(),
                                                    core_schema.no_info_plain_validator_function(
                                                        lambda value: value if isinstance(value, cls) else cls(value))])

        return core_schema.json_or_python_schema(json_schema=from_str_schema,
                                                 python_schema=core_schema.union_schema([
                                                     core_schema.is_instance_schema(cls),
                                                     from_str_schema]),
                                                 serialization=core_schema.plain_serializer_function_ser_schema(
                                                     lambda instance: str(instance)))

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema: core_schema.CoreSchema,
                                     handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        h = handler(core_schema.str_schema())
        h["example"] = str(cls("0.1.0"))
        return h

    @property
    def major(self) -> int:
        """
        The major version number of the version.

        :return: The major version number.
        :rtype: int
        """

        return self._major

    @major.setter
    def major(self, value: int | str | None):
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
    def minor(self, value: int | str | None):
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
    def patch(self, value: int | str | None):
        value = int(value)
        if value < 0:
            raise ValueError("Patch version must be a non-negative integer")
        self._patch = value

    @property
    def prerelease_type(self) -> str | None:
        """
        The prerelease type of the version.

        :return: The prerelease type.
        :rtype: Optional[PRERELEASE_TYPES]
        """

        return self._prerelease_type

    @prerelease_type.setter
    def prerelease_type(self, value: PRERELEASE_TYPES | None):
        if value is None:
            self._prerelease_type = None
            return
        if value not in PRERELEASE_TYPE_MAPPING.keys():
            raise ValueError(
                f"Invalid prerelease type: '{value}'\nAllowed values are: {list(PRERELEASE_TYPE_MAPPING.keys())}")
        self._prerelease_type = value

    @property
    def prerelease_number(self) -> int | None:
        """
        The prerelease number of the version.

        :return: The prerelease number.
        :rtype: Optional[int]
        """

        if self.prerelease_type is None:
            return None
        return self._prerelease_number

    @prerelease_number.setter
    def prerelease_number(self, value: int | str | None):
        if value is None:
            value = 0
        if value == "":
            value = 0
        value = int(value)
        if value < 0:
            raise ValueError("Prerelease number must be a non-negative integer")
        self._prerelease_number = value
