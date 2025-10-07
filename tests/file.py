import os
from abc import ABC, abstractmethod
from copy import deepcopy
from pathlib import Path
from typing import Any, Literal, Union

from typing_extensions import Self  # ToDo: Remove when Python 3.10 support is dropped

from pydantic import BaseModel, Field, PrivateAttr

DEFAULT_FILE_DIR = Path(os.getcwd())
FILE_MUST_EXIST_ANNOTATION = Union[bool, Literal["yes_print", "yes_warn", "yes_raise", "no_print", "no_warn", "no_warn_create", "no_create", "no"]]


class BaseFile(BaseModel, ABC):
    class Config:
        file_dir = ...
        file_name = ...
        file_suffix = None
        file_encoding = None
        file_newline = None
        file_must_exist = False
        file_indent = None

    class _InstanceConfig:
        """
        Instance configuration for file handling.

        Attributes:
            file_dir (str | Path): Directory where the file is located. If a string is provided, it will be converted to a Path object.
            file_name (str | None): Name of the file without suffix. If None, the class name in snake_case will be used.
            file_suffix (str | None): File extension. If None, no suffix will be used.
            file_encoding (str | None): File encoding. If None, the system default will be used.
            file_newline (str | None): Newline character(s). If None, the system default will be used.
            file_must_exist (FILE_MUST_EXIST_ANNOTATION): Whether the file must exist. True means "yes_print", False means "no", None means "no".
            file_indent (int | None): Number of spaces for indentation. If None or 0, no indentation will be used.
        """

        file_dir: str | Path
        file_name: str | None
        file_suffix: str | None
        file_encoding: str | None
        file_newline: str | None
        file_must_exist: FILE_MUST_EXIST_ANNOTATION
        file_indent: int | None

        def __init__(self, instance: "BaseFile") -> None:
            self.__instance = instance

        def __str__(self):
            return f"{self.__instance.__class__.__name__}({self.file_path})"

        def __dir__(self):
            keys = list(super().__dir__())
            for key in list(self.__instance._config.keys()):
                if key not in keys:
                    keys.append(key)
            for key in list(self.__instance.model_config.keys()):
                if key not in keys:
                    keys.append(key)
            return keys

        def __getattr__(self, item):
            if item in self.__instance._config:
                value = self.__instance._config[item]
            elif item in self.__instance.model_config:
                value = deepcopy(dict(self.__instance.model_config))[item]
            else:
                raise AttributeError(f"{item} not found in {self.__class__.__name__}!")

            # dynamic attributes
            if item == "file_dir" and value is Ellipsis:
                value = DEFAULT_FILE_DIR
            if item == "file_name" and value is Ellipsis:
                value = ''.join(
                    ['_' + c.lower() if c.isupper() else c for c in self.__instance.__class__.__name__]).lstrip('_')
            if item == "file_suffix" and value is not None:
                if not value.startswith('.'):
                    value = '.' + value
            if item == "file_must_exist":
                if value is True:
                    value = "yes_print"
                if value is False:
                    value = "no"
            return value

        def __setattr__(self, key, value):
            if key.startswith("_") or key in ["file_path"]:
                return super().__setattr__(key, value)
            self.__instance._config[key] = value
            return value

        @property
        def file_path(self) -> Path:
            """
            Full path to the file, constructed from directory, name, and suffix.

            :return: Path object representing the full file path.
            """

            fiel_path = Path(self.file_dir).with_name(self.file_name)
            if self.file_suffix:
                fiel_path = fiel_path.with_suffix(self.file_suffix)
            return fiel_path

    _config: dict[str, Any] = PrivateAttr(default_factory=dict)

    @property
    def config(self) -> _InstanceConfig:
        return self._InstanceConfig(instance=self)

    @classmethod
    def _read_file(cls) -> str:
        ...

    @classmethod
    @abstractmethod
    def _to_dict(cls) -> dict:
        ...

    @classmethod
    def load(cls) -> Self:
        print()

    def reload(self) -> None:
        print()

    @abstractmethod
    def _from_dict(self) -> str:
        ...

    def _write_file(self) -> None:
        ...

    def save(self) -> None:
        print()


class JsonFile(BaseFile):
    class Config:
        file_suffix = ".json"

    @classmethod
    def _to_dict(cls) -> dict:
        print()

    def _from_dict(self) -> str:
        print()

    ...


# class YamlFile(BaseFile):
#     ...
#
#
# class XmlFile(BaseFile):
#     ...


class ParentFile(JsonFile):
    ...
    # class Config:
    #     parent_file_attr = "qwe"


class SampleFile(ParentFile):
    # class Config:
    #     child_file_attr = "asd"

    attr_str1: str = Field(default=..., title="Test String 1", description="This is a test string attribute 1")
    attr_str2: str = Field(default=..., title="Test String 2", description="This is a test string attribute 2")
    attr_int1: int = Field(default=..., title="Test Integer 1", description="This is a test integer attribute 1")
    attr_int2: int = Field(default=..., title="Test Integer 2", description="This is a test integer attribute 2")
    attr_float1: float = Field(default=..., title="Test Float 1", description="This is a test float attribute 1")
    attr_float2: float = Field(default=..., title="Test Float 2", description="This is a test float attribute 2")
    attr_bool1: bool = Field(default=..., title="Test Boolean 1", description="This is a test boolean attribute 1")
    attr_bool2: bool = Field(default=..., title="Test Boolean 2", description="This is a test boolean attribute 2")


if __name__ == "__main__":
    sample = SampleFile(
        attr_str1="Hello",
        attr_str2="World",
        attr_int1=42,
        attr_int2=7,
        attr_float1=3.14,
        attr_float2=2.71,
        attr_bool1=True,
        attr_bool2=False
    )
    print()
