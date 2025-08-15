import sys
from typing_extensions import Self
from warnings import warn
from pathlib import Path
from typing import Any, Union, Literal, Callable, Generator, Optional, Type, Mapping

from pydantic import BaseModel
from pydantic._internal._model_construction import ModelMetaclass

from wiederverwendbar.pydantic.file_config.errors import FileConfigLoadingError, FileConfigSavingError
from wiederverwendbar.warnings import FileNotFoundWarning

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
        cls: Union[Type[FileConfig], Type] = super().__new__(mcs, name, bases, attrs)

        # set the loader for the class
        cls._loader = loader

        # set the saver for the class
        cls._saver = saver

        return cls


class FileConfig(BaseModel, metaclass=FileConfigMeta):
    _loader: dict[str, tuple[list[str], _LODER_FUNC_TYPE]]
    _saver: dict[str, _SAVER_FUNC_TYPE]
    # _file_path: Optional[Path] = None
    # _mode: Optional[str] = None
    # _encoding: Optional[str] = None
    # _newline: Optional[str] = None
    # _loader_kwargs: dict[str, Any] = {}
    # _saver_kwargs: dict[str, Any] = {}

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
             **loader_kwargs) -> Self:
        # set default file path
        if file_path is None:
            file_path = Path(Path.cwd() / cls.__name__.lower())
        elif type(file_path) is str:
            if file_path == "":
                file_path = Path(Path.cwd() / cls.__name__.lower())
            file_path = Path(file_path)
        file_path = file_path.absolute()

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
