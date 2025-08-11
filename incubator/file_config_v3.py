import json
import sys
from abc import ABCMeta, abstractmethod, ABC
from copy import deepcopy
from pathlib import Path

from typing import Any, Union, Iterable, Optional, Literal, Mapping
from warnings import warn

from pydantic import BaseModel, PrivateAttr
from typing_extensions import Self

from wiederverwendbar.warnings import FileNotFoundWarning


class FileConfigError(Exception):
    ...


class FileConfigLoadingError(FileConfigError):
    ...


class FileConfigSavingError(FileConfigError):
    ...


class BaseFileHandlerMeta(ABCMeta):
    def __new__(mcs, name: str, bases: tuple[type, ...], namespace: dict[str, Any]):
        if (bases[0] if len(bases) > 0 else None) is ABC:
            return super().__new__(mcs, name, bases, namespace)

        # check attributes
        mcs.check_attribute_is_set(name=name, bases=bases, namespace=namespace, attribute_name="mode", attribute_type=str)
        mcs.check_attribute_is_set(name=name, bases=bases, namespace=namespace, attribute_name="default_suffix", attribute_type=str)
        mcs.check_attribute_is_set(name=name, bases=bases, namespace=namespace, attribute_name="default_content", attribute_type=str)

        return super().__new__(mcs, name, bases, namespace)

    @classmethod
    def check_attribute_is_set(mcs, name: str, bases: tuple[type, ...], namespace: dict[str, Any], attribute_name: str, attribute_type: type) -> None:
        attribute = namespace.get(attribute_name, ...)
        if attribute is None:
            for base in bases:
                attribute = getattr(base, attribute_name, ...)
        if attribute is ...:
            raise AttributeError(f"Class {name} must define a '{attribute_name}' attribute.")
        if type(attribute) is not attribute_type:
            raise TypeError(f"Class {name} must define a '{attribute_name}' attribute of type {attribute_type.__name__}, got {type(attribute).__name__}.")


_MUST_EXIST_ANNOTATION_LITERAL = Literal[
    "yes_print",
    "yes_warn",
    "yes_raise",
    "no_print",
    "no_warn",
    "no"]
_MUST_EXIST_ANNOTATION = Union[None, bool, _MUST_EXIST_ANNOTATION_LITERAL]


class BaseFileHandler(ABC, metaclass=BaseFileHandlerMeta):
    mode: str
    default_suffix: str
    default_content: str

    def __init__(self,
                 cls: type["FileConfigV3"],
                 file_path: Union[None, Path, str],
                 encoding: Optional[str],
                 newline: Optional[str],
                 must_exist: _MUST_EXIST_ANNOTATION,
                 loads_kwargs: Optional[dict[str, Any]],
                 dumps_kwargs: Optional[dict[str, Any]],
                 **kwargs):
        self.cls = cls
        self._file_path = file_path
        self.encoding = encoding
        self.newline = newline
        self._must_exist = must_exist
        self._loads_kwargs = loads_kwargs
        self._dumps_kwargs = dumps_kwargs
        self.kwargs = kwargs

    @property
    def file_path(self) -> Path:
        file_path = self._file_path
        if file_path is None:
            file_path = Path(Path.cwd() / self.cls.__name__.lower())
        elif type(file_path) is str:
            if file_path == "":
                file_path = Path(Path.cwd() / self.cls.__name__.lower())
            file_path = Path(file_path)
        if not file_path.suffix:
            file_path = file_path.with_suffix(self.default_suffix)
        return file_path.absolute()

    @file_path.setter
    def file_path(self, file_path: Union[None, Path, str]) -> None:
        self._file_path = file_path

    @property
    def must_exist(self) -> _MUST_EXIST_ANNOTATION_LITERAL:
        must_exist = self._must_exist
        if must_exist is None:
            must_exist = True
        if must_exist:
            must_exist = "yes_raise"
        else:
            must_exist = "no"
        if must_exist not in ("yes_print", "yes_warn", "yes_raise", "no_print", "no_warn", "no"):
            raise ValueError(f"Invalid value for must_exist: {must_exist}. Must be one of: "
                             "'yes_print', 'yes_warn', 'yes_raise', 'no_print', 'no_warn', 'no'.")
        return must_exist

    @must_exist.setter
    def must_exist(self, must_exist: _MUST_EXIST_ANNOTATION) -> None:
        self._must_exist = must_exist

    @property
    def loads_kwargs(self) -> dict[str, Any]:
        loads_kwargs = self._loads_kwargs
        if loads_kwargs is None:
            loads_kwargs = {}
        return deepcopy(loads_kwargs)

    @loads_kwargs.setter
    def loads_kwargs(self, kwargs: Optional[dict[str, Any]]) -> None:
        self._loads_kwargs = deepcopy(kwargs)

    @property
    def dumps_kwargs(self) -> dict[str, Any]:
        dumps_kwargs = self._dumps_kwargs
        if dumps_kwargs is None:
            dumps_kwargs = {}
        return deepcopy(dumps_kwargs)

    @dumps_kwargs.setter
    def dumps_kwargs(self, kwargs: Optional[dict[str, Any]]) -> None:
        self._dumps_kwargs = deepcopy(kwargs)

    def read(self) -> str:
        if self.file_path.is_file():
            # read content from file
            with self.file_path.open("r", encoding=self.encoding, newline=self.newline) as file:
                return file.read()
        # handle if file not exists
        msg = f"{self.cls.__class__.__name__} '{self.file_path}' does not exist."
        if self.must_exist == "yes_print":
            print(msg)
            sys.exit(1)
        elif self.must_exist == "yes_warn":
            warn(msg, FileNotFoundWarning)
            sys.exit(1)
        elif self.must_exist == "yes_raise":
            raise FileNotFoundError(msg)
        elif self.must_exist == "no_warn":
            warn(msg, FileNotFoundWarning)
        return self.default_content

    def write(self, content: str) -> None:
        print()

    def load(self,
             strict: Optional[bool] = None,
             from_attributes: Optional[bool] = None,
             context: Optional[Any] = None,
             by_alias: Optional[bool] = None,
             by_name: Optional[bool] = None,
             overwrite_data: Optional[dict[Any, Any]] = None) -> "FileConfigV3":
        """
        Load the content of the file and parse it into a dictionary.
        This method should be overridden by subclasses to implement specific loading logic.
        """

        try:
            # read the content from the file
            content = self.read()

            # parse the content into a dictionary
            data = self.loads(content)

            # overwrite data
            if overwrite_data is not None:
                for k, v in overwrite_data.items():
                    data[k] = v

            # validate and create the model instance
            model = self.cls.model_validate(data,
                                            strict=strict,
                                            from_attributes=from_attributes,
                                            context=context,
                                            by_alias=by_alias,
                                            by_name=by_name)
            return model
        except Exception as e:
            raise FileConfigLoadingError(f"Error loading {self.cls.__name__} from file '{self.file_path}': {e}") from e

    @abstractmethod
    def loads(self, content: str) -> dict[Any, Any]:
        ...

    def dump(self) -> str:
        """
        Dump the data into a string representation.
        This method should be overridden by subclasses to implement specific dumping logic.
        """

        print()

    @abstractmethod
    def dumps(self, data: dict[Any, Any]) -> str:
        ...


class JsonFileHandler(BaseFileHandler):
    mode = "json"
    default_suffix = ".json"
    default_content = "{}"

    def loads(self, content: str) -> dict[Any, Any]:
        return json.loads(content, **self.loads_kwargs)

    def dumps(self, data: dict[Any, Any]) -> str:
        print()


class FileConfigV3(BaseModel):
    # dict of available file handlers
    _available_handlers: dict[str, type[BaseFileHandler]] = PrivateAttr(default_factory=dict)
    # current file handler
    _handler: Union[None, BaseFileHandler] = PrivateAttr(default=None)

    def __init_subclass__(cls, handler: Union[None, type[BaseFileHandler], Iterable[type[BaseFileHandler]]] = None, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if handler is None:
            handler = []
        if not isinstance(handler, Iterable):
            handler = [handler]
        _available_handlers = getattr(cls, "_available_handlers")
        if type(_available_handlers) is not dict:
            _available_handlers = {}
        _available_handlers = deepcopy(_available_handlers)
        for h in handler:
            # noinspection PyUnreachableCode
            if not issubclass(h, BaseFileHandler):
                raise TypeError(f"Handler {h} is not a valid BaseFileHandler subclass.")
            _available_handlers[h.mode] = h

        if len(_available_handlers) == 0:
            raise ValueError(f"Class {cls.__name__} must define at least one file handler.")
        # set the handler
        cls._available_handlers = _available_handlers

    @property
    def mode(self) -> Optional[str]:
        if self._handler is None:
            return None
        return self._handler.mode

    @mode.setter
    def mode(self, mode: str) -> None:
        if mode not in self._available_handlers:
            raise ValueError(f"No handler found for mode '{mode}'. Available modes: {list(self._available_handlers.keys())}.")

        # get the current handler attributes
        file_path = self.handler.file_path if self.handler else None
        encoding = self.handler.encoding if self.handler else None
        newline = self.handler.newline if self.handler else None
        must_exist = self.handler.must_exist if self.handler else None
        loads_kwargs = self.handler.loads_kwargs if self.handler else None
        dumps_kwargs = self.handler.dumps_kwargs if self.handler else None
        kwargs = self.handler.kwargs if self.handler else {}

        # set the current handler
        self._handler = self._available_handlers[mode](cls=self.__class__,
                                                       file_path=file_path,
                                                       encoding=encoding,
                                                       newline=newline,
                                                       must_exist=must_exist,
                                                       loads_kwargs=loads_kwargs,
                                                       dumps_kwargs=dumps_kwargs,
                                                       **kwargs)

    @property
    def handler(self) -> Optional[BaseFileHandler]:
        return self._handler

    @classmethod
    def load(cls,
             mode: Optional[str] = None,
             file_path: Union[None, Path, str] = None,
             encoding: Optional[str] = None,
             newline: Optional[str] = None,
             must_exist: _MUST_EXIST_ANNOTATION = None,
             loads_kwargs: Optional[dict[str, Any]] = None,
             dumps_kwargs: Optional[dict[str, Any]] = None,
             strict: Optional[bool] = None,
             from_attributes: Optional[bool] = None,
             context: Optional[Any] = None,
             by_alias: Optional[bool] = None,
             by_name: Optional[bool] = None,
             overwrite_data: Optional[dict[Any, Any]] = None,
             create: bool = False,
             **handler_kwargs) -> Self:
        # set default mode
        if mode is None:
            mode = list(cls._available_handlers.keys())[0]
        if mode not in cls._available_handlers:
            raise ValueError(f"No handler found for mode '{mode}'. Available modes: {list(cls._available_handlers.keys())}.")

        # create the handler
        handler = cls._available_handlers[mode](cls=cls,
                                                file_path=file_path,
                                                encoding=encoding,
                                                newline=newline,
                                                must_exist=must_exist,
                                                loads_kwargs=loads_kwargs,
                                                dumps_kwargs=dumps_kwargs,
                                                **handler_kwargs)

        # load the configuration
        self = handler.load(strict=strict,
                            from_attributes=from_attributes,
                            context=context,
                            by_alias=by_alias,
                            by_name=by_name,
                            overwrite_data=overwrite_data)

        # set the handler
        self._handler = handler

        # if create is True, save the configuration to the file if it does not exist
        if create and not self.handler.file_path.is_file():
            self.save()

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

    def reload(self) -> None:
        ...

    def save(self,
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
            data = self.model_dump(mode="json",
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

        print()


class Config(FileConfigV3, handler=JsonFileHandler):
    ...


class ChildConfig(Config):
    ...


if __name__ == '__main__':
    config = Config.load()
    # config.mode = "json"
    print()
