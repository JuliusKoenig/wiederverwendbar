import atexit
import logging
from abc import ABCMeta
from typing import Any, Optional, Union

from wiederverwendbar.functions.find_class_method import find_class_method

logger = logging.getLogger(__name__)


class Singleton(ABCMeta):
    """
    Singleton metaclass
    """

    singleton_map: dict[str, Any] = {}
    singleton_order: dict[str, int] = {}
    delete_all_on_exit = True
    delete_ordered_on_exit = True

    def __new__(cls, name, bases, attrs, order: Optional[int] = None):
        # get __init__ method
        __init__ = attrs.pop("__init__", None)
        if __init__ is None:
            __init__ = find_class_method(bases, "__init__")

        # wrap __init__ method
        def singleton__init__(self, *args, **kwargs):
            _order = order
            if _order is None:
                _order = Singleton.get_next_order()
            self_name = self.__class__.__name__
            if _order in Singleton.singleton_order.values():
                raise RuntimeError(f"Singleton order {_order} already initialized. Use {self_name}() to get the instance.")
            if self_name not in Singleton.singleton_map:
                Singleton.singleton_map[self_name] = self
                Singleton.singleton_order[self_name] = _order
                logger.debug(f"Singleton '{self_name}' with order {_order} initialized.")
                if __init__ is not None:
                    __init__(self, *args, **kwargs)
            else:
                raise RuntimeError(f"Singleton {self_name} already initialized. Use {self_name}() to get the instance.")

        attrs["__singleton__"] = True

        # check if __singleton__ is set on bases
        singleton_set = False
        for _base in bases:
            if hasattr(_base, "__singleton__"):
                singleton_set = True
                break

        if not singleton_set:
            attrs["__init__"] = singleton__init__

        return super().__new__(cls, name, bases, attrs)

    def __call__(cls, *args, init: bool = False, **kwargs):
        if init:
            if cls.__name__ not in Singleton.singleton_map:
                return super().__call__(*args, **kwargs)
            else:
                raise RuntimeError(f"Singleton {cls.__name__} already initialized. Use {cls.__name__}() to get the instance.")
        else:
            if cls.__name__ in Singleton.singleton_map:
                return cls.get_by_name(cls.__name__)
            else:
                raise RuntimeError(f"Singleton {cls.__name__} not initialized. Call {cls.__name__}(init=True) first.")

    @classmethod
    def get_all(cls, ordered: bool = True) -> dict[str, Any]:
        """
        Return all singletons in map

        :param ordered: Return ordered map
        :return: Singleton map
        """

        if ordered:
            singleton_map = {k: v for k, v in sorted(cls.singleton_map.items(), key=lambda item: cls.singleton_order[item[0]])}
        else:
            singleton_map = cls.singleton_map

        return singleton_map

    @classmethod
    def get_by_name(cls, name: str) -> Any:
        """
        Get singleton by name

        :param name: Name of singleton
        :return: SingletonInstance
        """

        current = cls.get_all().get(name, None)
        if current is None:
            raise RuntimeError(f"Singleton {name} not found.")
        return current

    @classmethod
    def get_by_type(cls, t: Union[type, str]) -> Any:
        """
        Get singleton by type

        :param t: Type of singleton
        :return: SingletonInstance
        """

        if isinstance(t, str):
            searching_name = t
        elif isinstance(t, type):
            searching_name = t.__name__
        else:
            raise TypeError(f"Type of 't' must be 'str' or 'type', not '{type(t)}'.")
        for name, instance in cls.get_all().items():
            if isinstance(t, str):
                # get all bases
                bases = instance.__class__.__bases__
                for base in bases:
                    if base.__name__ == searching_name:
                        return instance
            elif isinstance(t, type):
                if isinstance(instance, t):
                    return instance
        raise RuntimeError(f"Singleton {searching_name} not found.")

    @classmethod
    def get_by_order(cls, order: int) -> Any:
        """
        Get singleton by order

        :param order: Order of singleton
        :return: SingletonInstance
        """

        for name, _order in cls.singleton_order.items():
            if _order == order:
                return cls.get_by_name(name)
        raise RuntimeError(f"Singleton order {order} not found.")

    @classmethod
    def get_next_order(cls) -> int:
        """
        Get next order for singleton

        :return: Next order
        """

        if len(cls.singleton_order) == 0:
            return 1
        else:
            return max(cls.singleton_order.values()) + 1

    @classmethod
    def delete_all(cls, ordered: Optional[bool] = None):
        """
        Delete all singletons in map
        """

        # if ordered is None, delete by class attribute
        if ordered is None:
            ordered = cls.delete_ordered_on_exit

        singleton_names = list(cls.get_all(ordered=ordered).keys())
        singleton_names.reverse()
        for name in singleton_names:
            cls.delete_by_name(name)

    @classmethod
    def delete_by_name(cls, name: str):
        """
        Delete singleton by name

        :param name: Name of singleton
        """

        current = cls.get_all().get(name, None)
        if current is None:
            raise RuntimeError(f"Singleton {name} not found.")
        logger.debug(f"Singleton '{name}' deleted.")
        del cls.singleton_map[name]

    @classmethod
    def delete_by_type(cls, t: Union[type, str]):
        """
        Delete singleton by type

        :param t: Type of singleton
        """

        current = cls.get_by_type(t)
        if current is None:
            raise RuntimeError(f"Singleton {t} not found.")
        logger.debug(f"Singleton '{current.__class__.__name__}' deleted.")
        del cls.singleton_map[current.__class__.__name__]

    @classmethod
    def delete_by_order(cls, order: int):
        """
        Delete singleton by order

        :param order: Order of singleton
        """

        current = cls.get_by_order(order)
        if current is None:
            raise RuntimeError(f"Singleton order {order} not found.")
        logger.debug(f"Singleton '{current.__class__.__name__}' deleted.")
        del cls.singleton_map[current.__class__.__name__]


def _on_exit():
    """
    On exit hook
    """

    logger.debug("Running on exit hook.")

    if Singleton.delete_all_on_exit:
        Singleton.delete_all()


atexit.register(_on_exit)
