import json
import yaml
import xml
import sys
from warnings import warn
from pathlib import Path
from typing import Any, Union, Literal, Callable, Generator, Optional

from pydantic import BaseModel, create_model
from pydantic._internal._model_construction import ModelMetaclass

from wiederverwendbar.default import Default
from wiederverwendbar.warnings import FileNotFoundWarning


class FileConfig(BaseModel):
    def __init__(self,
                 file_path: Union[Path, str, None] = None,
                 file_postfix: str = ".json",
                 file_must_exist: Union[bool, Literal["yes_print", "yes_warn", "yes_raise", "no"]] = "no",
                 **overwrite_data: Any):
        if file_path is None:
            file_path = Path(Path.cwd() / self.__class__.__name__.lower()).with_suffix(file_postfix)
        else:
            file_path = Path(file_path)
            if file_path.suffix == "":
                file_path = file_path.with_suffix(file_postfix)
        file_path = file_path.absolute()

        # read data from file
        if file_path.is_file():
            with file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        elif file_path.is_dir():
            raise ValueError(f"{self.__class__.__name__} file path '{file_path}' is a directory.")
        else:
            if file_must_exist is True:
                file_must_exist = "yes_raise"
            elif file_must_exist is False:
                file_must_exist = "no"
            msg = f"{self.__class__.__name__} file '{file_path}' not found."
            if file_must_exist == "yes_print":
                print(msg)
                sys.exit(1)
            elif file_must_exist == "yes_warn":
                warn(msg, FileNotFoundWarning)
                sys.exit(1)
            elif file_must_exist == "yes_raise":
                raise FileNotFoundError(msg)
            data = {}

        # overwrite data
        for k, v in overwrite_data.items():
            data[k] = v

        super().__init__(**data)

        self._file_path = file_path

    @property
    def file_path(self) -> Path:
        """
        File path

        :return: Path
        """

        return self._file_path

    def save(self, validate: bool = True, indent: int = 4, encoding: str = "utf-8"):
        if validate:
            validate_model_info = {}
            for field_name, field_info in self.model_fields.items():
                validate_model_info[field_name] = (field_info.annotation, field_info)
            validate_model = create_model(f"{self.__class__.__name__}_Validate", **validate_model_info)

            params = self.model_dump()
            validated = validate_model(**params)
            self_json = validated.model_dump_json(indent=indent)
        else:
            self_json = self.model_dump_json(indent=indent)

        with self.file_path.open("w", encoding=encoding) as file:
            file.write(self_json)


class FileConfigLoadingError(Exception):
    ...


_LOADER: dict[str, tuple[list[str], Callable[..., Any]]] = {}


def register_loader(mode: str, *suffixes: str) -> Callable[[Callable[[str], dict[str, Any]]], Callable[[str], dict[str, Any]]]:
    """
    Decorator to register a loader method for specific file suffixes.
    """

    def decorator(func: Callable[[str], dict[str, Any]]):
        if mode in _LOADER:
            raise ValueError(f"Loader for mode '{mode}' is already registered.")
        if not callable(func):
            raise TypeError(f"Function '{func.__name__}' is not callable.")
        _LOADER[mode] = (list(suffixes), func)
        return func

    return decorator


class FileConfigMeta(ModelMetaclass):
    def __new__(mcs, name, bases, attrs):
        loader: dict[str, tuple[list[str], Callable[..., Any]]] = {}

        # get loaders from base classes
        for base in bases:
            l = getattr(base, "_loader", {})
            loader.update(l)

        # get global loaders
        global _LOADER
        loader.update(_LOADER)
        _LOADER = {}

        cls = super().__new__(mcs, name, bases, attrs)

        cls._loader = loader

        return cls


class FileConfigV2(BaseModel, metaclass=FileConfigMeta):
    @classmethod
    @register_loader("json", ".json")
    def _load_json(cls, content: str) -> dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise FileConfigLoadingError(f"Invalid JSON content: {e}") from e

    @classmethod
    @register_loader("yaml", ".yaml", ".yml")
    def _load_yaml(cls, content: str) -> dict[str, Any]:
        return {}

    @classmethod
    @register_loader("xml", ".xml")
    def _load_xml(cls, content: str) -> dict[str, Any]:
        return {}

    @classmethod
    def _get_loader(cls, search_suffix: str = "") -> Generator[tuple[str, Callable[..., Any]], Any, None]:
        """
        Get the loader function for the specified mode.
        """

        for suffixes, loader in cls._loader.values():
            for suffix in suffixes:
                if search_suffix == "":
                    yield suffix, loader
                else:
                    if suffix == search_suffix:
                        yield suffix, loader

    @classmethod
    def load(cls,
             file_path: Union[Default, Path, str] = Default(),
             encoding: Union[Default, str, None] = Default(),
             newline: Union[Default, str, None] = Default(),
             must_exist: Union[Default, bool, Literal[
                 "yes_print",
                 "yes_warn",
                 "yes_raise",
                 "no_warn",
                 "no_warn_create",
                 "no_create",
                 "no"]] = Default(),
             strict: Optional[bool] = None,
             from_attributes: Optional[bool] = None,
             context: Optional[Any] = None,
             by_alias: Optional[bool] = None,
             by_name: Optional[bool] = None,
             **overwrite_data: Any):
        # set default file path
        if type(file_path) is Default:
            file_path = Path(Path.cwd() / cls.__name__.lower())
        elif type(file_path) is str:
            if file_path == "":
                file_path = Path(Path.cwd() / cls.__name__.lower())
            file_path = Path(file_path)

        # set default encoding
        if type(encoding) is Default:
            encoding = None

        # set default newline
        if type(newline) is Default:
            newline = None

        # set default must_exist behavior
        if type(must_exist) is Default:
            must_exist = "yes_raise"
        if must_exist is True:
            must_exist = "yes_raise"
        elif must_exist is False:
            must_exist = "no"

        # get loader for file suffix
        current_loader = None
        tried_suffixes = []
        for suffix, loader in cls._get_loader(file_path.suffix):
            if suffix in tried_suffixes:
                continue
            tried_suffixes.append(suffix)
            if file_path.with_suffix(suffix).is_file():
                file_path = file_path.with_suffix(suffix)
                current_loader = loader
                break

        # handle file existence
        create = False
        content = ""
        if not file_path.is_file():
            msg = f"{cls.__class__.__name__} '{file_path}({', '.join(['*' + str(s) for s in tried_suffixes])})' not found."
            if must_exist == "yes_print":
                print(msg)
                sys.exit(1)
            elif must_exist == "yes_warn":
                warn(msg, FileNotFoundWarning)
                sys.exit(1)
            elif must_exist == "yes_raise":
                raise FileNotFoundError(msg)
            elif must_exist == "no_warn":
                warn(msg, FileNotFoundWarning)
                # ToDo: handle no file found
            elif must_exist == "no_warn_create":
                warn(msg, FileNotFoundWarning)
                create = True
            elif must_exist == "no":
                # ToDo: handle no file found
                pass

        # handle no loader found
        if current_loader is None:
            raise AttributeError(f"No loader registered for suffix '{file_path.suffix}' in class '{cls.__name__}'.")

        # read content from file
        with file_path.open("r", encoding=encoding, newline=newline) as file:
            content = file.read()

        # load data using the loader
        data = current_loader(cls=cls, content=content)

        # overwrite data
        for k, v in overwrite_data.items():
            data[k] = v

        # validate and create the model instance
        self = cls.model_validate(data,
                                  strict=strict,
                                  from_attributes=from_attributes,
                                  context=context,
                                  by_alias=by_alias,
                                  by_name=by_name)

        self._file_path = file_path

        return self


class Config(FileConfigV2):
    asd: int = 123
    qwe: str = "qwe"
    yxc: bool = False


if __name__ == '__main__':
    # config = Config.parse_file(file_path="test", file_must_exist="yes_raise")
    # config = Config()
    c = Config.load()
    print()
