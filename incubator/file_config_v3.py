from copy import deepcopy


from typing import Any, Union, Iterable

from pydantic import BaseModel, PrivateAttr



class BaseFileHandlerMeta(type):
    def __new__(mcs, name: str, bases: tuple[type, ...], namespace: dict[str, Any]):
        if len(bases) == 0:
            return super().__new__(mcs, name, bases, namespace)

        # check mode attribute
        mode = namespace.get("mode", None)
        if mode is None:
            for base in bases:
                mode = getattr(base, "mode", None)
        if type(mode) is not str:
            raise TypeError(f"Class {name} must define a 'mode' attribute of type str, got {type(mode).__name__}.")

        return super().__new__(mcs, name, bases, namespace)


class BaseFileHandler(metaclass=BaseFileHandlerMeta):
    mode: str


class JsonFileHandler(BaseFileHandler):
    mode = "json"

class FileConfigV3(BaseModel):
    _handler: dict[str, type[BaseFileHandler]] = PrivateAttr(default_factory=dict)

    def __init_subclass__(cls, handler: Union[None, type[BaseFileHandler], Iterable[type[BaseFileHandler]]] = None, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if handler is None:
            handler = []
        if not isinstance(handler, Iterable):
            handler = [handler]
        _handler = getattr(cls, "_handler")
        if type(_handler) is not dict:
            _handler = {}
        _handler = deepcopy(_handler)
        for h in handler:
            # noinspection PyUnreachableCode
            if not issubclass(h, BaseFileHandler):
                raise TypeError(f"Handler {h} is not a valid BaseFileHandler subclass.")
            _handler[h.mode] = h
        # set the handler
        cls._handler = _handler


class Config(FileConfigV3, handler=JsonFileHandler):
    ...

class ChildConfig(Config):
    ...


if __name__ == '__main__':
    config = Config()
    # config.
    print()
