import json
import yaml
import xml
import sys
from typing_extensions import Self
from warnings import warn
from pathlib import Path
from typing import Any, Union, Literal, Callable, Generator, Optional, Type, Mapping

from pydantic import BaseModel, Field
from pydantic._internal._model_construction import ModelMetaclass

from wiederverwendbar.warnings import FileNotFoundWarning


class FileConfigError(Exception):
    ...


class FileConfigLoadingError(FileConfigError):
    ...


class FileConfigSavingError(FileConfigError):
    ...


_LODER_FUNC_TYPE = Callable[[Type["FileConfigV2"], str, ...], dict[str, Any]]
_LOADER: dict[str, tuple[list[str], _LODER_FUNC_TYPE]] = {}
_SAVER_FUNC_TYPE = Callable[["FileConfigV2", dict[str, Any], ...], str]
_SAVER: dict[str, _SAVER_FUNC_TYPE] = {}


def register_loader(mode: str, *suffixes: str) -> Callable[[_LODER_FUNC_TYPE], _LODER_FUNC_TYPE]:
    """
    Decorator to register a loader method for specific file suffixes.

    :param mode: The mode for which the loader is registered (e.g., "json", "yaml", "xml").
    :param suffixes: The file suffixes that this loader can handle (e.g., ".json", ".yaml", ".xml").
    :return: A decorator that registers the loader function.
    """

    def decorator(func: _LODER_FUNC_TYPE):
        if mode in _LOADER:
            raise ValueError(f"Loader for mode '{mode}' is already registered.")
        # noinspection PyUnreachableCode
        if not callable(func):
            raise TypeError(f"Function '{func.__name__}' is not callable.")
        _LOADER[mode] = (list(suffixes), func)
        return func

    return decorator


def register_saver(mode: str) -> Callable[[_SAVER_FUNC_TYPE], _SAVER_FUNC_TYPE]:
    """
    Decorator to register a saver method for a specific mode.

    :param mode: The mode for which the saver is registered (e.g., "json", "yaml", "xml").
    :return: A decorator that registers the saver function.
    """

    def decorator(func: _SAVER_FUNC_TYPE):
        if mode in _SAVER:
            raise ValueError(f"Saver for mode '{mode}' is already registered.")
        # noinspection PyUnreachableCode
        if not callable(func):
            raise TypeError(f"Function '{func.__name__}' is not callable.")
        _SAVER[mode] = func
        return func

    return decorator


class FileConfigMeta(ModelMetaclass):
    def __new__(mcs, name, bases, attrs):
        loader: dict[str, tuple[list[str], _LODER_FUNC_TYPE]] = {}

        # get loaders from base classes
        for base in bases:
            l = getattr(base, "_loader", {})
            loader.update(l)

        # get global loaders
        global _LOADER
        loader.update(_LOADER)
        _LOADER = {}

        saver: dict[str, _SAVER_FUNC_TYPE] = {}
        # get savers from base classes
        for base in bases:
            s = getattr(base, "_saver", {})
            saver.update(s)

        # get global savers
        global _SAVER
        saver.update(_SAVER)
        _SAVER = {}

        # create the class
        cls: Union[Type[FileConfigV2], Type] = super().__new__(mcs, name, bases, attrs)

        # set the loader for the class
        cls._loader = loader

        # set the saver for the class
        cls._saver = saver

        return cls


class FileConfigV2(BaseModel, metaclass=FileConfigMeta):
    _loader: dict[str, tuple[list[str], _LODER_FUNC_TYPE]]
    _saver: dict[str, _SAVER_FUNC_TYPE]
    _file_path: Optional[Path] = None
    _mode: Optional[str] = None
    _encoding: Optional[str] = None
    _newline: Optional[str] = None
    _loader_kwargs: dict[str, Any] = {}
    _saver_kwargs: dict[str, Any] = {}

    @classmethod
    @register_loader("json", ".json")
    def _load_json(cls, content: str, **kwargs) -> dict[str, Any]:
        return json.loads(content, **kwargs)

    @register_saver("json")
    def _save_json(self, data: dict[str, Any], **kwargs) -> str:
        return json.dumps(data, **kwargs)

    @classmethod
    @register_loader("yaml", ".yaml", ".yml")
    def _load_yaml(cls, content: str, **kwargs) -> dict[str, Any]:
        return {}

    @classmethod
    @register_loader("xml", ".xml")
    def _load_xml(cls, content: str, **kwargs) -> dict[str, Any]:
        return {}

    @classmethod
    def _get_loader(cls, search_suffix: str = "") -> Generator[tuple[str, str, _LODER_FUNC_TYPE], None, None]:
        """
        Get the loader function for the specified mode.

        :param search_suffix: The file suffix to search for. If empty, all suffixes will be returned.
        :return: A generator yielding tuples of (mode, suffix, loader).
        """

        for mode, suffixes_loader in cls._loader.items():
            suffixes, loader = suffixes_loader
            for suffix in suffixes:
                if search_suffix == "":
                    yield mode, suffix, loader
                else:
                    if suffix == search_suffix:
                        yield mode, suffix, loader

    @classmethod
    def _get_saver(cls, mode: str) -> Optional[_SAVER_FUNC_TYPE]:
        """
        Get the saver function for the specified mode.

        :param mode: The mode for which to get the saver function.
        :return: The saver function or None if not found.
        """

        return cls._saver.get(mode, None)

    @classmethod
    def _convert_file_path(cls, file_path: Union[None, Path, str] = None) -> Path:
        """
        Convert the file path to an absolute Path object.

        :param file_path: The file path to convert.
        :return: An absolute Path object or None if the input is None.
        """

        if file_path is None:
            file_path = Path(Path.cwd() / cls.__name__.lower())
        elif type(file_path) is str:
            if file_path == "":
                file_path = Path(Path.cwd() / cls.__name__.lower())
            file_path = Path(file_path)
        return file_path.absolute()

    @property
    def file_path(self) -> Path:
        """
        File path

        :return: Path
        """

        return self._file_path

    @file_path.setter
    def file_path(self, value: Union[None, Path, str]) -> None:
        """
        Set the file path for the configuration.

        :param value: The new file path as a Path or string.
        """

        if isinstance(value, str):
            value = Path(value)
        if type(value) is Path:
            value = value.absolute()
        self._file_path = value

    @property
    def mode(self) -> Optional[str]:
        """
        File mode

        :return: str or None
        """

        return self._mode

    @mode.setter
    def mode(self, value: Optional[str]) -> None:
        """
        Set the file mode for the configuration.

        :param value: The new file mode as a string.
        """

        self._mode = value

    @property
    def encoding(self) -> Optional[str]:
        """
        File encoding

        :return: str or None
        """

        return self._encoding

    @encoding.setter
    def encoding(self, value: Optional[str]) -> None:
        """
        Set the file encoding for the configuration.

        :param value: The new file encoding as a string.
        """

        self._encoding = value

    @property
    def newline(self) -> Optional[str]:
        """
        File newline character

        :return: str or None
        """

        return self._newline

    @newline.setter
    def newline(self, value: Optional[str]) -> None:
        """
        Set the file newline character for the configuration.

        :param value: The new file newline character as a string.
        """

        self._newline = value

    @property
    def loader_kwargs(self) -> dict[str, Any]:
        """
        Loader keyword arguments

        :return: dict[str, Any]
        """

        return self._loader_kwargs

    @loader_kwargs.setter
    def loader_kwargs(self, value: dict[str, Any]) -> None:
        """
        Set the loader keyword arguments for the configuration.

        :param value: The new loader keyword arguments as a dictionary.
        """

        self._loader_kwargs = value

    @property
    def saver_kwargs(self) -> dict[str, Any]:
        """
        Saver keyword arguments

        :return: dict[str, Any]
        """

        return self._saver_kwargs

    @saver_kwargs.setter
    def saver_kwargs(self, value: dict[str, Any]) -> None:
        """
        Set the saver keyword arguments for the configuration.

        :param value: The new saver keyword arguments as a dictionary.
        """

        self._saver_kwargs = value


    @classmethod
    def load(cls,
             file_path: Union[None, Path, str] = None,
             encoding: Union[None, str, None] = None,
             newline: Union[None, str, None] = None,
             must_exist: Union[bool, Literal[
                 "yes_print",
                 "yes_warn",
                 "yes_raise",
                 "no_print",
                 "no_warn",
                 "no_warn_create",
                 "no_create",
                 "no"]] = True,
             strict: Optional[bool] = None,
             from_attributes: Optional[bool] = None,
             context: Optional[Any] = None,
             by_alias: Optional[bool] = None,
             by_name: Optional[bool] = None,
             overwrite_data: Optional[dict[Any, Any]] = None,
             **loader_kwargs) -> Self:
        """
        Load a configuration from a file.

        :param file_path: The file path to load the configuration from. If Default(), it will use the class name as the file name.
        :param encoding: The encoding to use when reading the file. If Default(), it will use the system default encoding.
        :param newline: The newline character to use when reading the file. If Default(), it will use the system default newline.
        :param must_exist: Indicates whether the file must exist. True will translate to "yes_raise" behavior.
        If False, it will translate to "no" behavior.
        If "yes_print", it will print a warning if the file does not exist and exit with code 1.
        If "yes_warn", it will trigger a warning if the file does not exist and exit with code 1.
        If "yes_raise", it will raise a FileNotFoundError if the file does not exist.
        If "no_print", it will print a warning if the file does not exist but continue execution.
        If "no_warn", it will trigger a warning if the file does not exist but continue execution.
        If "no_warn_create", it will trigger a warning if the file does not exist but continue execution and create the file.
        If "no_create", it will continue execution and create the file if it does not exist.
        If "no", it will continue execution without checking if the file exists.
        :param strict: Whether to enforce types strictly.
        :param from_attributes: Whether to extract data from object attributes.
        :param context: Additional context to pass to the validator.
        :param by_alias: Whether to use the field's alias when validating against the provided input data.
        :param by_name: Whether to use the field's name when validating against the provided input data
        :param overwrite_data: A dictionary of data to overwrite in the loaded file.
        :param loader_kwargs: Additional keyword arguments to pass to the loader function.
        :return: Self
        """

        # set default file path
        file_path = cls._convert_file_path(file_path=file_path)

        # set default must_exist behavior
        if must_exist is True:
            must_exist = "yes_raise"
        elif must_exist is False:
            must_exist = "no"

        # get loader for file suffix
        current_mode = None
        current_loader: Optional[_LODER_FUNC_TYPE] = None
        tried_suffixes = []
        for mode, suffix, loader in cls._get_loader(file_path.suffix):
            if suffix in tried_suffixes:
                continue
            tried_suffixes.append(suffix)
            if file_path.with_suffix(suffix).is_file():
                file_path = file_path.with_suffix(suffix)
                current_mode = mode
                current_loader = loader
                break

        # handle file existence
        create = False
        data = {}
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
            elif must_exist == "no_warn_create":
                warn(msg, FileNotFoundWarning)
                create = True
            elif must_exist == "no_create":
                create = False
            elif must_exist == "no":
                pass
        else:
            # read content from file
            with file_path.open("r", encoding=encoding, newline=newline) as file:
                content = file.read()

            # handle no loader found
            if current_loader is None:
                raise AttributeError(f"No loader registered for suffix '{file_path.suffix}' in class '{cls.__name__}'.")

            # load data using the loader
            try:
                data = current_loader(cls, content, **loader_kwargs)
            except Exception as e:
                raise FileConfigLoadingError(f"Error loading {cls.__name__} from file '{file_path}': {e}") from e

        # overwrite data
        if overwrite_data is not None:
            for k, v in overwrite_data.items():
                data[k] = v

        # validate and create the model instance
        self = cls.model_validate(data,
                                  strict=strict,
                                  from_attributes=from_attributes,
                                  context=context,
                                  by_alias=by_alias,
                                  by_name=by_name)

        # set the file path, mode, encoding and newline
        self._file_path = file_path
        self._mode = current_mode
        self._encoding = encoding
        self._newline = newline

        return self

    # noinspection PyMethodOverriding
    def validate(self,
                 include: Union[set[int], set[str], Mapping[int, Union[bool, Any]], Mapping[str, Union[bool, Any]], None] = None,
                 exclude: Union[set[int], set[str], Mapping[int, Union[bool, Any]], Mapping[str, Union[bool, Any]], None] = None,
                 context: Optional[Any] = None,
                 by_alias: Optional[bool] = None,
                 exclude_unset: bool = False,
                 exclude_defaults: bool = False,
                 exclude_none: bool = False,
                 round_trip: bool = False,
                 warnings: Union[Literal["none", "warn", "error"], bool] = True,
                 fallback: Optional[Any] = None,
                 serialize_as_any: bool = False) -> dict[str, Any]:
        """
        Validate the model and return a dictionary representation of the model.
        This method uses the `model_dump` method to get the model data and then validates it

        :param file_path: The file path to load the configuration from. If Default(), it will use the class name as the file name.
        :param include: A set of fields to include in the output.
        :param exclude: A set of fields to exclude from the output.
        :param context: Additional context to pass to the serializer.
        :param by_alias: Whether to use the field's alias in the dictionary key if defined.
        :param exclude_unset: Whether to exclude fields that have not been explicitly set.
        :param exclude_defaults: Whether to exclude fields that are set to their default value.
        :param exclude_none: Whether to exclude fields that have a value of None.
        :param round_trip: If True, dumped values should be valid as input for non-idempotent types such as Json[T].
        :param warnings: How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors,
        "error" raises a [PydanticSerializationError][pydantic_core.PydanticSerializationError].
        :param fallback: A function to call when an unknown value is encountered. If not provided,
        a [PydanticSerializationError][pydantic_core.PydanticSerializationError] error is raised.
        :param serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.
        :return: dict[str, Any]
        """

        self_dict = self.model_dump(mode="json",
                                    include=include,
                                    exclude=exclude,
                                    context=context,
                                    by_alias=by_alias,
                                    exclude_unset=exclude_unset,
                                    exclude_defaults=exclude_defaults,
                                    exclude_none=exclude_none,
                                    round_trip=round_trip,
                                    warnings=warnings,
                                    fallback=fallback,
                                    serialize_as_any=serialize_as_any)

        self.__class__(**self_dict)

        return self_dict

    def save(self,
             file_path: Union[None, Path, str] = None,
             encoding: Union[None, str, None] = None,
             newline: Union[None, str, None] = None,
             mode: Union[None, str] = None,
             validate: bool = True,
             create_parent_dirs: bool = True,
             include: Union[set[int], set[str], Mapping[int, Union[bool, Any]], Mapping[str, Union[bool, Any]], None] = None,
             exclude: Union[set[int], set[str], Mapping[int, Union[bool, Any]], Mapping[str, Union[bool, Any]], None] = None,
             context: Optional[Any] = None,
             by_alias: Optional[bool] = None,
             exclude_unset: bool = False,
             exclude_defaults: bool = False,
             exclude_none: bool = False,
             round_trip: bool = False,
             warnings: Union[Literal["none", "warn", "error"], bool] = True,
             fallback: Optional[Any] = None,
             serialize_as_any: bool = False,
             overwrite_data: Optional[dict[Any, Any]] = None,
             **saver_kwargs) -> None:
        """
        Save the model to a file.

        :param file_path: The file path to save the model to. If None, the file path must be set in the class.
        :param encoding: The encoding to use when saving the file. If None, the encoding is used from the class otherwise system default.
        :param newline: The newline character to use when saving the file. If None, the newline is used from the class otherwise system default.
        :param mode: The mode to use for saving the model. If None, the mode must be set in the class.
        :param validate: Whether to validate the model before saving. If True, the model will be validated using the `validate` method.
        :param create_parent_dirs: Whether to create parent directories if they do not exist.
        :param include: A set of fields to include in the output.
        :param exclude: A set of fields to exclude from the output.
        :param context: Additional context to pass to the serializer.
        :param by_alias: Whether to use the field's alias in the dictionary key if defined.
        :param exclude_unset: Whether to exclude fields that have not been explicitly set.
        :param exclude_defaults: Whether to exclude fields that are set to their default value.
        :param exclude_none: Whether to exclude fields that have a value of None.
        :param round_trip: If True, dumped values should be valid as input for non-idempotent types such as Json[T].
        :param warnings: How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors,
        "error" raises a [PydanticSerializationError][pydantic_core.PydanticSerializationError].
        :param fallback: A function to call when an unknown value is encountered. If not provided,
        a [PydanticSerializationError][pydantic_core.PydanticSerializationError] error is raised.
        :param serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.
        :param overwrite_data: Additional data to overwrite in the model before saving.
        :param saver_kwargs: Additional keyword arguments to pass to the saver function.
        :return: None
        """

        # set default file path
        if file_path is None:
            file_path = self.file_path
        file_path = self._convert_file_path(file_path=file_path)
        if file_path is None:
            raise ValueError(f"File path must be set in the class or passed as an argument.")

        # set default encoding
        if encoding is None:
            encoding = self.encoding

        # set default newline
        if newline is None:
            newline = self.newline

        # set default mode
        if mode is None:
            mode = self.mode
        if mode is None:
            raise ValueError(f"Mode must be set in the class or passed as an argument.")

        # get saver
        current_saver = self._get_saver(mode)
        if current_saver is None:
            raise AttributeError(f"No saver registered for mode '{mode}' in class '{self.__class__.__name__}'.")

        # validate
        if validate:
            data = self.validate(include=include,
                                 exclude=exclude,
                                 context=context,
                                 by_alias=by_alias,
                                 exclude_unset=exclude_unset,
                                 exclude_defaults=exclude_defaults,
                                 exclude_none=exclude_none,
                                 round_trip=round_trip,
                                 warnings="error",
                                 fallback=fallback,
                                 serialize_as_any=serialize_as_any)
        else:
            data = self.model_dump(mode=mode,
                                   include=include,
                                   exclude=exclude,
                                   context=context,
                                   by_alias=by_alias,
                                   exclude_unset=exclude_unset,
                                   exclude_defaults=exclude_defaults,
                                   exclude_none=exclude_none,
                                   round_trip=round_trip,
                                   warnings=warnings,
                                   fallback=fallback,
                                   serialize_as_any=serialize_as_any)

        # overwrite data
        if overwrite_data is not None:
            for k, v in overwrite_data.items():
                data[k] = v

        # save data using the saver
        try:
            content = current_saver(self, data, **saver_kwargs)
        except Exception as e:
            raise FileConfigSavingError(f"Error saving {self.__class__.__name__} to file '{file_path}': {e}") from e

        # create parent directories if needed
        if create_parent_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        # write content to file
        with file_path.open("w", encoding=encoding, newline=newline) as file:
            file.write(content)

        # update file path, mode, encoding and newline
        self._file_path = file_path
        self._mode = mode
        self._encoding = encoding
        self._newline = newline


class Config(FileConfigV2):
    asd: int = Field(123, le=150)
    qwe: str = "qwe"
    yxc: bool = False


if __name__ == '__main__':
    # config = Config.parse_file(file_path="test", file_must_exist="yes_raise")
    # config = Config()
    c = Config.load()
    c.asd = 120
    c.save(exclude=["qwe"])
    print()
