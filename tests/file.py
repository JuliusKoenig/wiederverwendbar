import logging
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Literal, Union, Optional
from warnings import warn
from typing_extensions import Self  # ToDo: Remove when Python 3.10 support is dropped

from pydantic import BaseModel, Field, PrivateAttr, ValidationError
from wiederverwendbar.warnings import FileNotFoundWarning

try:
    from wiederverwendbar.rich import RichConsole as Console
except ImportError:
    from wiederverwendbar.console import Console

logger = logging.getLogger(__name__)

DEFAULT_FILE_DIR = Path(os.getcwd())
FILE_MUST_EXIST_ANNOTATION = Union[bool, Literal["yes_print", "yes_raise", "no_print", "no_warn", "no_ignore"]]
FILE_ON_VALIDATION_ERROR_ANNOTATION = Literal["print", "raise"]  # ToDo: "ignore", "warn"?


def validation_error_make_pretty_lines(exception: ValidationError) -> list[str]:
    errors = exception.errors()
    lines = []
    for error in errors:
        loc_str = ""
        for l in error.get("loc", ()):
            if isinstance(l, int):
                loc_str += f"[{l}]"
            else:
                if loc_str:
                    loc_str += "."
                loc_str += str(l)
        msg = error.get("msg", "")
        typ = error.get("type", "")
        line = f"Error at '{loc_str}': {msg} (type={typ})"
        lines.append(line)
    return lines


class BaseFile(BaseModel, ABC):
    class Config:
        file_dir = ...
        file_name = ...
        file_suffix = None
        file_encoding = None
        file_newline = None
        file_must_exist = False
        file_on_validation_error = "print"
        file_indent = None
        file_console = Console()

    class _InstanceConfig:
        """
        Instance configuration for file handling.

        Attributes:
            file_dir (str | Path): Directory where the file is located. If a string is provided, it will be converted to a Path object.
            file_name (str | None): Name of the file without suffix. If None, the class name in snake_case will be used.
            file_suffix (str | None): File extension. If None, no suffix will be used.
            file_encoding (str | None): File encoding. If None, the system default will be used.
            file_newline (str | None): Newline character(s). If None, the system default will be used.
            file_must_exist (FILE_MUST_EXIST_ANNOTATION): Whether the file must exist. True means "yes_print", False means "no_ignore"
            file_indent (int | None): Number of spaces for indentation. If None or 0, no indentation will be used.
        """

        file_dir: str | Path
        file_name: str | None
        file_suffix: str | None
        file_encoding: str | None
        file_newline: str | None
        file_must_exist: FILE_MUST_EXIST_ANNOTATION
        file_on_validation_error: FILE_ON_VALIDATION_ERROR_ANNOTATION
        file_indent: int | None
        file_console: Console

        def __init__(self,
                     cls: type["BaseFile"],
                     instance_config: dict[str, Any]) -> None:
            self.__cls = cls
            self.__instance_config = instance_config

        def __str__(self):
            return f"{self.__cls.__name__}('{self.file_path}')"

        def __dir__(self):
            keys = list(super().__dir__())
            for key in list(self.__instance_config.keys()):
                if key not in keys:
                    keys.append(key)
            for key in list(self.__cls.model_config.keys()):
                if key not in keys:
                    keys.append(key)
            return keys

        def __getattr__(self, item):
            if item in self.__instance_config:
                value = self.__instance_config[item]
            elif item in self.__cls.model_config:
                value = dict(self.__cls.model_config)[item]
            else:
                raise AttributeError(f"Item '{item}' not found in {self.__cls_name}!")
            # dynamic attributes
            if item == "file_dir" and value is Ellipsis:
                value = DEFAULT_FILE_DIR
            if item == "file_name" and value is Ellipsis:
                value = ''.join(
                    ['_' + c.lower() if c.isupper() else c for c in self.__cls.__name__]).lstrip('_')
            if item == "file_suffix" and value is not None:
                if not value.startswith('.'):
                    value = '.' + value
            if item == "file_must_exist":
                if value is True:
                    value = "yes_print"
                if value is False:
                    value = "no_ignore"
            return value

        def __setattr__(self, key, value):
            if key.startswith("_") or key in ["file_path"]:
                return super().__setattr__(key, value)
            self.__instance_config[key] = value
            return None

        @property
        def file_path(self) -> Path:
            """
            Full path to the file, constructed from directory, name, and suffix.

            :return: Path object representing the full file path.
            """

            fiel_path = Path(self.file_dir).with_name(self.file_name)
            if self.file_suffix:
                fiel_path = fiel_path.with_suffix(self.file_suffix)
            return fiel_path.absolute()

    _config: dict[str, Any] = PrivateAttr(default_factory=dict)

    @property
    def config(self) -> _InstanceConfig:
        return self._InstanceConfig(cls=self.__class__,
                                    instance_config=self._config)

    @classmethod
    def _read_file(cls, config: _InstanceConfig) -> str | None:
        logger.debug(f"Reading {cls.__name__} from '{config.file_path}' ...")

        # handle file existence
        content = None
        if not config.file_path.is_file():
            msg = f"File {config} not found."
            if config.file_must_exist == "yes_print":
                if config.file_console:
                    config.file_console.error(msg)
                else:
                    print(f"ERROR: {msg}")
                sys.exit(1)
            elif config.file_must_exist == "yes_raise":
                raise FileNotFoundError(msg)
            elif config.file_must_exist == "no_print":
                if config.file_console:
                    config.file_console.warning(msg)
                else:
                    print(f"WARNING: {msg}")
            elif config.file_must_exist == "no_warn":
                warn(msg, FileNotFoundWarning)
            elif config.file_must_exist == "no_ignore":
                ...
            else:
                raise RuntimeError(f"Invalid value for file_must_exist: {config.file_must_exist}")
        else:
            with config.file_path.open(mode="r",
                                       encoding=config.file_encoding,
                                       newline=config.file_newline) as file:
                content = file.read()
        return content

    @classmethod
    @abstractmethod
    def _to_dict(cls, content: str, config: _InstanceConfig) -> dict:
        ...

    @classmethod
    def load(cls,
             overwrite: dict[str, Any] | None = None,
             **instance_config: Any) -> Self:
        # get instance config
        config = cls._InstanceConfig(cls=cls, instance_config=instance_config)

        # read file
        content = cls._read_file(config=config)

        # parse content
        if content is not None:
            data = cls._to_dict(content=content, config=config)
        else:
            data = {}

        # overwrite data
        if overwrite is not None:
            for key, value in overwrite.items():
                data[key] = value

        # create instance
        try:
            instance = cls(**data)
        except ValidationError as e:
            if config.file_on_validation_error == "raise":
                raise e
            elif config.file_on_validation_error == "print":
                lines = validation_error_make_pretty_lines(exception=e)
                if config.file_console:
                    config.file_console.error(f"Validation Error in {config}", *lines)
                else:
                    print(f"ERROR: Validation Error in {config}")
                    for line in lines:
                        print("  " + line)
                sys.exit(1)
            else:
                raise RuntimeError(f"Invalid value for file_on_validation_error: {config.file_on_validation_error}")

        # set instance config
        instance._config = instance_config

        return instance

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

    class Sub(BaseModel):
        sub_attr_str: str = Field(default=..., title="Sub Attribute 1", description="This is a sub attribute 1")
        sub_attr_int: int = Field(default=..., title="Sub Attribute 2", description="This is a sub attribute 2")
        sub_attr_float: float = Field(default=..., title="Sub Attribute 3", description="This is a sub attribute 3")
        sub_attr_bool: bool = Field(default=..., title="Sub Attribute 4", description="This is a sub attribute 4")

    attr_str1: str = Field(default=..., title="Test String 1", description="This is a test string attribute 1")
    attr_str2: str = Field(default=..., title="Test String 2", description="This is a test string attribute 2")
    attr_int1: int = Field(default=..., title="Test Integer 1", description="This is a test integer attribute 1")
    attr_int2: int = Field(default=..., title="Test Integer 2", description="This is a test integer attribute 2")
    attr_float1: float = Field(default=..., title="Test Float 1", description="This is a test float attribute 1")
    attr_float2: float = Field(default=..., title="Test Float 2", description="This is a test float attribute 2")
    attr_bool1: bool = Field(default=..., title="Test Boolean 1", description="This is a test boolean attribute 1")
    attr_bool2: bool = Field(default=..., title="Test Boolean 2", description="This is a test boolean attribute 2")
    attr_sub: Sub = Field(default=..., title="Test Sub Model", description="This is a test sub model attribute")
    attr_list_sub: list[Sub] = Field(
        default_factory=list,
        title="Test List of Sub Models",
        description="This is a test list of sub model attributes"
    )


if __name__ == "__main__":
    # sample = SampleFile(
    #     attr_str1="Hello",
    #     attr_str2="World",
    #     attr_int1=42,
    #     attr_int2=7,
    #     attr_float1=3.14,
    #     attr_float2=2.71,
    #     attr_bool1=True,
    #     attr_bool2=False
    # )

    sample = SampleFile.load(
        overwrite={
            "attr_str1": "Hello",
            "attr_str2": "World",
            "attr_int1": 42,
            "attr_int2": 7,
            "attr_float1": 3.14,
            "attr_float2": 2.71,
            "attr_bool1": True,
            "attr_bool2": False,
            "attr_sub": {
                "sub_attr_str": "asd",
                "sub_attr_int": 123,
                "sub_attr_float": 1.23,
                "sub_attr_bool": True
            },
            "attr_list_sub": [
                {
                    "sub_attr_str": "qwe",
                    "sub_attr_int": 456,
                    "sub_attr_float": 4.56,
                    "sub_attr_bool": False
                },
                {
                    "sub_attr_str": "zxc",
                    "sub_attr_int": 789,
                    "sub_attr_float": 7.89,
                    "sub_attr_bool": True
                }
            ]
        },
        file_name="custom",
        file_must_exist="no_print"
    )

    print()
