import logging
import os
import sys
from abc import ABC, abstractmethod
from copy import deepcopy
from pathlib import Path
from typing import Any, Literal, Union, Mapping

from warnings import warn
from typing_extensions import Self  # ToDo: Remove when Python 3.10 support is dropped

from pydantic import BaseModel, PrivateAttr, ValidationError
from wiederverwendbar.pydantic.validation_error_make_pretty_lines import validation_error_make_pretty_lines
from wiederverwendbar.warnings import FileNotFoundWarning

try:
    from wiederverwendbar.rich import RichConsole as Console
except ImportError:
    from wiederverwendbar.console import Console

logger = logging.getLogger(__name__)

DEFAULT_FILE_DIR = Path(os.getcwd())
FILE_MUST_EXIST_ANNOTATION = Union[bool, Literal["yes_print", "yes_raise", "no_print", "no_warn", "no_ignore"]]
FILE_ON_ERROR_ANNOTATION = Literal["print", "raise"]
FILE_SAVE_ON_LOAD_ANNOTATION = Literal["if_not_exist", "no"]


class BaseFile(BaseModel, ABC):
    class Config:
        file_dir = ...
        file_name = ...
        file_suffix = None
        file_encoding = None
        file_newline = None
        file_overwrite = None
        file_must_exist = False
        file_save_on_load = "no"
        file_on_reading_error = "print"
        file_on_to_dict_error = "print"
        file_on_validation_error = "print"
        file_on_from_dict_error = "print"
        file_on_saving_dict_error = "print"
        file_console = Console()
        file_include = None
        file_exclude = None
        file_context = None
        file_by_alias = None
        file_exclude_unset = False
        file_exclude_defaults = False
        file_exclude_none = False

    class _InstanceConfig:
        """
        Instance configuration for file handling.

        Attributes:
            file_dir (str | Path): Directory where the file is located. If a string is provided, it will be converted to a Path object.
            file_name (str | None): Name of the file without suffix. If None, the class name in snake_case will be used.
            file_suffix (str | None): File extension. If None, no suffix will be used.
            file_encoding (str | None): File encoding. If None, the system default will be used.
            file_newline (str | None): Newline character(s). If None, the system default will be used.
            file_overwrite (dict[str, Any] | None): Dictionary of values to overwrite after loading the file.
            file_must_exist (FILE_MUST_EXIST_ANNOTATION): Whether the file must exist. True means "yes_print", False means "no_ignore"
            file_save_on_load (FILE_SAVE_ON_LOAD_ANNOTATION): Whether to save the file upon loading if it does not exist.
            file_on_reading_error (FILE_ON_ERROR_ANNOTATION): Action to take on reading error.
            file_on_to_dict_error (FILE_ON_ERROR_ANNOTATION): Action to take on to_dict conversion error.
            file_on_validation_error (FILE_ON_ERROR_ANNOTATION): Action to take on validation error.
            file_on_from_dict_error (FILE_ON_ERROR_ANNOTATION): Action to take on from_dict conversion error.
            file_on_saving_dict_error (FILE_ON_ERROR_ANNOTATION): Action to take on saving dict error.
            file_console (Console): Console object for logging messages. If None, print statements will be used.
            file_include (set[int] | set[str] | Mapping[int, bool | Any] | Mapping[str, bool | Any] | None): Fields to include when saving.
            file_exclude (set[int] | set[str] | Mapping[int, bool | Any] | Mapping[str, bool | Any] | None): Fields to exclude when saving.
            file_context (Any | None): Context to pass to Pydantic serialization methods.
            file_by_alias (bool | None): Whether to use field aliases when saving.
            file_exclude_unset (bool): Whether to exclude unset fields when saving.
            file_exclude_defaults (bool): Whether to exclude fields with default values when saving.
            file_exclude_none (bool): Whether to exclude fields with None values when saving.
        """

        file_dir: str | Path
        file_name: str | None
        file_suffix: str | None
        file_encoding: str | None
        file_newline: str | None
        file_overwrite: dict[str, Any] | None
        file_must_exist: FILE_MUST_EXIST_ANNOTATION
        file_save_on_load: FILE_SAVE_ON_LOAD_ANNOTATION
        file_on_reading_error: FILE_ON_ERROR_ANNOTATION
        file_on_to_dict_error: FILE_ON_ERROR_ANNOTATION
        file_on_validation_error: FILE_ON_ERROR_ANNOTATION
        file_on_from_dict_error: FILE_ON_ERROR_ANNOTATION
        file_on_saving_dict_error: FILE_ON_ERROR_ANNOTATION
        file_console: Console
        file_include: set[int] | set[str] | Mapping[int, bool | Any] | Mapping[str, bool | Any] | None
        file_exclude: set[int] | set[str] | Mapping[int, bool | Any] | Mapping[str, bool | Any] | None
        file_context: Any | None
        file_by_alias: bool | None
        file_exclude_unset: bool
        file_exclude_defaults: bool
        file_exclude_none: bool

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
    def _create(cls, data: dict[str, Any], config: _InstanceConfig, error_message: str) -> Self:
        try:
            instance = cls(**data)
        except ValidationError as e:
            if config.file_on_validation_error == "raise":
                logger.error(e)
                raise e
            elif config.file_on_validation_error == "print":
                lines = validation_error_make_pretty_lines(exception=e)
                logger.error("\n  ".join((error_message, *lines)))
                if config.file_console:
                    config.file_console.error(error_message, *lines)
                else:
                    print(f"ERROR: {error_message}")
                    for line in lines:
                        print("  " + line)
                sys.exit(1)
            else:
                raise RuntimeError(f"Invalid value for file_on_validation_error: {config.file_on_validation_error}")
        return instance

    @classmethod
    def _read_file(cls, config: _InstanceConfig) -> str | None:
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
    def _load(cls, config: _InstanceConfig) -> dict[str, Any]:
        # read file
        logger.debug(f"Reading {config} ...")
        try:
            content = cls._read_file(config=config)
        except Exception as e:
            msg = f"Error reading {config}: {e}"
            logger.error(msg)
            if config.file_on_reading_error == "raise":
                raise e
            elif config.file_on_reading_error == "print":
                if config.file_console:
                    config.file_console.error(msg)
                else:
                    print(f"ERROR: {msg}")
                sys.exit(1)
            else:
                raise RuntimeError(f"Invalid value for file_on_reading_error: {config.file_on_reading_error}")
        logger.debug(f"Reading {config} ... Done")

        # parse content
        if content is not None:
            logger.debug(f"Converting content of {config} to dict ...")
            try:
                data = cls._to_dict(content=content, config=config)
            except Exception as e:
                msg = f"Error converting content of {config} to dict: {e}"
                logger.error(msg)
                if config.file_on_to_dict_error == "raise":
                    raise e
                elif config.file_on_to_dict_error == "print":
                    if config.file_console:
                        config.file_console.error(msg)
                    else:
                        print(f"ERROR: {msg}")
                    sys.exit(1)
                else:
                    raise RuntimeError(f"Invalid value for file_on_to_dict_error: {config.file_on_to_dict_error}")
            logger.debug(f"Converting content of {config} to dict ... Done")
        else:
            logger.debug(f"No content in {config} ...")
            data = {}

        # overwrite data
        if config.file_overwrite is not None:
            for key, value in config.file_overwrite.items():
                data[key] = value

        return data

    @classmethod
    def load(cls, **instance_config: Any) -> Self:
        # get instance config
        config = cls._InstanceConfig(cls=cls, instance_config=instance_config)

        logger.debug(f"Loading {config} ...")

        # call internal load method
        data = cls._load(config=config)

        # validate and create instance
        instance = cls._create(data=data, config=config, error_message=f"Loading error in {config}")

        # set instance config
        instance._config = instance_config

        logger.debug(f"Loading {config} ... Done")

        # save file if not exist and wanted
        if config.file_save_on_load == "if_not_exist" and not config.file_path.is_file():
            logger.debug(f"Saving {config} because it did not exist ...")
            instance.save()
            logger.debug(f"Saving {config} because it did not exist ... Done")

        return instance

    def reload(self, **extra_config: Any) -> None:
        # create config from instance config and extra config
        for key, value in self._config.items():
            if key in extra_config:
                continue
            if type(value) in [list, dict]:
                value = deepcopy(value)
            extra_config[key] = value
        config = self._InstanceConfig(cls=self.__class__, instance_config=extra_config)

        logger.debug(f"Reloading {config} ...")

        # call internal load method
        data = self._load(config=config)

        # validate and create temporary instance
        instance = self._create(data=data, config=config, error_message=f"Reloading error in {config}")

        # update self
        for field_name in self.__class__.model_fields.keys():
            value = getattr(instance, field_name)
            setattr(self, field_name, value)

        logger.debug(f"Reloading {config} ... Done")

    @abstractmethod
    def _from_dict(self, data: dict[str, Any], config: _InstanceConfig) -> str:
        ...

    def _write_file(self, content: str, config: _InstanceConfig) -> None:
        with config.file_path.open(mode="w",
                                   encoding=config.file_encoding,
                                   newline=config.file_newline) as file:
            file.write(content)

    def save(self, **extra_config: Any) -> None:
        # create config from instance config and extra config
        for key, value in self._config.items():
            if key in extra_config:
                continue
            if type(value) in [list, dict]:
                value = deepcopy(value)
            extra_config[key] = value
        config = self._InstanceConfig(cls=self.__class__, instance_config=extra_config)

        logger.debug(f"Saving {config} ...")

        # convert instance to dict
        data = self.model_dump(
            mode="json",
            include=config.file_include,
            exclude=config.file_exclude,
            context=config.file_context,
            by_alias=config.file_by_alias,
            exclude_unset=config.file_exclude_unset,
            exclude_defaults=config.file_exclude_defaults,
            exclude_none=config.file_exclude_none,
            round_trip=False,
            warnings=False,
            fallback=None,
            serialize_as_any=False
        )

        # validate
        self._create(data=data, config=config, error_message=f"Saving error in {config}")

        # convert dict to string
        logger.debug(f"Converting {config} to string ...")
        try:
            content = self._from_dict(data=data, config=config)
        except Exception as e:
            msg = f"Error converting {config} to string: {e}"
            logger.error(msg)
            if config.file_on_from_dict_error == "raise":
                raise e
            elif config.file_on_from_dict_error == "print":
                if config.file_console:
                    config.file_console.error(msg)
                else:
                    print(f"ERROR: {msg}")
                sys.exit(1)
            else:
                raise RuntimeError(f"Invalid value for file_on_from_dict_error: {config.file_on_from_dict_error}")
        logger.debug(f"Converting {config} to string ... Done")

        # write file
        logger.debug(f"Writing {config} ...")
        try:
            self._write_file(content=content, config=config)
        except Exception as e:
            msg = f"Error writing {config}: {e}"
            logger.error(msg)
            if config.file_on_saving_dict_error == "raise":
                raise e
            elif config.file_on_saving_dict_error == "print":
                if config.file_console:
                    config.file_console.error(msg)
                else:
                    print(f"ERROR: {msg}")
                sys.exit(1)
            else:
                raise RuntimeError(f"Invalid value for file_on_saving_dict_error: {config.file_on_saving_dict_error}")
        logger.debug(f"Writing {config} ... Done")

        logger.debug(f"Saving {config} ... Done")
