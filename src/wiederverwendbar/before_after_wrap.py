import inspect
import logging
from abc import ABCMeta
from functools import wraps
from typing import Optional

from wiederverwendbar.functions.find_class_method import find_class_method

logger = logging.getLogger(__name__)


class WrappedClass(ABCMeta):
    def __new__(cls, name, bases, attrs, order: Optional[int] = None):
        logger.debug(f"Creating {cls.__name__} '{name}'")

        # iterate over all attributes
        for attr_name, attr in attrs.items():
            if getattr(attr, "__ba_wrapped__", False):
                # get before and after names
                before_names = getattr(attr, "__ba_before__")
                after_names = getattr(attr, "__ba_after__")

                # get base attr if include_base is True
                base_before_names = []
                base_after_names = []
                if getattr(attr, "__ba_include_base__", False):
                    base_attr = find_class_method(bases, attr_name)
                    if base_attr is not None:
                        if getattr(base_attr, "__ba_wrapped__", False):
                            base_before_names = getattr(base_attr, "__ba_before__")
                            base_after_names = getattr(base_attr, "__ba_after__")
            else:
                # get base attr
                base_attr = find_class_method(bases, attr_name)
                if base_attr is None:
                    continue
                if not getattr(base_attr, "__ba_wrapped__", False):
                    continue
                if not getattr(base_attr, "__ba_include_inherited__", True):
                    continue

                # get before and after names from base attr
                before_names = []
                after_names = []
                base_before_names = getattr(base_attr, "__ba_before__")
                base_after_names = getattr(base_attr, "__ba_after__")

            # get before and after methods
            before_methods = _get_methods([*base_before_names, *before_names], attrs, bases)
            after_methods = _get_methods([*base_after_names, *after_names], attrs, bases)

            # wrap method
            attrs[attr_name] = _wrap(before_methods, after_methods)(attr)

        return ABCMeta.__new__(cls, name, bases, attrs)


def _get_methods(method_names: list[str], attrs: dict[str, callable], bases: list[type] = None):
    if bases is None:
        bases = []
    methods = []
    for method_name in method_names:
        if method_name in attrs:
            method = attrs[method_name]
        else:
            method = find_class_method(bases, method_name)
        if method is None:
            raise ValueError(f"Method '{method_name}' not found.")
        methods.append(method)
    return methods


def _get_signatures(func: callable, before_methods: list[callable], after_methods: list[callable]) -> tuple[inspect.Signature, list[inspect.Signature], list[inspect.Signature]]:
    # get before method signatures
    before_method_signatures = []
    for before_method in before_methods:
        if not callable(before_method):
            raise ValueError("before_method must be a callable.")

        logger.debug(f"Gather before_method '{before_method.__name__}' signature.")
        before_method_signatures.append(inspect.signature(before_method))

    # get after method signatures
    after_method_signatures = []
    for after_method in after_methods:
        if not callable(after_method):
            raise ValueError("after_method must be a callable.")

        logger.debug(f"Gather after_method '{after_method.__name__}' signature.")
        after_method_signatures.append(inspect.signature(after_method))

    # get func signature
    func_signature = inspect.signature(func)

    return func_signature, before_method_signatures, after_method_signatures


def _wrapper(*args,
             func: callable,
             before_methods: list[callable],
             after_methods: list[callable],
             func_signature: inspect.Signature,
             before_method_signatures: list[inspect.Signature],
             after_method_signatures: list[inspect.Signature],
             **kwargs):
    # add before_result to kwargs
    if "__ba_before_result__" in kwargs:
        raise ValueError("__ba_before_result__ is a reserved keyword.")
    kwargs["__ba_before_result__"] = None
    if "__ba_result__" in kwargs:
        raise ValueError("__ba_result__ is a reserved keyword.")
    kwargs["__ba_result__"] = None
    if "__ba_after_result__" in kwargs:
        raise ValueError("__ba_after_result__ is a reserved keyword.")
    kwargs["__ba_after_result__"] = None

    def bind(s: inspect.Signature) -> dict[str, any]:
        if "__ba_before_result__" in kwargs:
            if "__ba_before_result__" not in s.parameters:
                del kwargs["__ba_before_result__"]
        if "__ba_result__" in kwargs:
            if "__ba_result__" not in s.parameters:
                del kwargs["__ba_result__"]
        if "__ba_after_result__" in kwargs:
            if "__ba_after_result__" not in s.parameters:
                del kwargs["__ba_after_result__"]

        return s.bind(*args, **kwargs).arguments

    # get __ba_use__ flag
    __ba_use__ = kwargs.pop("__ba_use__", True)
    if not __ba_use__:
        mapped_params = bind(func_signature)
        return func(**mapped_params)

    # get __ba_use_before__ flag
    __ba_use_before__ = kwargs.pop("__ba_use_before__", True)

    # get __ba_use_after__ flag
    __ba_use_after__ = kwargs.pop("__ba_use_after__", True)

    # call before_methods
    if __ba_use_before__:
        for bm in before_methods:
            # get before_method_signature
            bms = before_method_signatures[before_methods.index(bm)]

            # map args and kwargs to before_method_signature
            mapped_params = bind(bms)

            # call before_method
            logger.debug(f"Call before_method '{bm.__name__}'")
            kwargs["__ba_before_result__"] = bm(**mapped_params)

    # map args and kwargs to func_signature
    mapped_params = bind(func_signature)

    # call func
    logger.debug(f"Call function '{func.__name__}'")
    __ba_result__ = func(**mapped_params)
    kwargs["__ba_result__"] = __ba_result__

    # call after_methods
    if __ba_use_after__:
        for am in after_methods:
            # get after_method_signature
            ams = after_method_signatures[after_methods.index(am)]

            # map args and kwargs to after_method_signature
            mapped_params = bind(ams)

            # call after_method
            logger.debug(f"Call after_method '{am.__name__}'")
            kwargs["__ba_after_result__"] = am(**mapped_params)

    return __ba_result__


def _wrap(before_methods: list[callable], after_methods: list[callable]):
    def decorator(func):
        # get signatures
        func_signature, before_method_signatures, after_method_signatures = _get_signatures(func, before_methods, after_methods)

        return wraps(func)(lambda *args, **kwargs: _wrapper(*args,
                                                            func=func,
                                                            before_methods=before_methods,
                                                            after_methods=after_methods,
                                                            func_signature=func_signature,
                                                            before_method_signatures=before_method_signatures,
                                                            after_method_signatures=after_method_signatures,
                                                            **kwargs))

    return decorator


def wrap(before=None, after=None, include_base=True, include_inherited=True):
    if before is None and after is None:
        raise ValueError("before and after cannot be None at the same time.")

    # get before names
    before_names = []
    if callable(before):
        # convert to list
        before = [before]
    if type(before) is str:
        before = [before]
    if before is not None:
        for b in before:
            if callable(b):
                before_names.append(b.__name__)
            elif type(b) is str:
                before_names.append(b)
            else:
                raise ValueError("before must be a list of callables or strings.")

    # get after names
    after_names = []
    if callable(after):
        # convert to list
        after = [after]
    if type(after) is str:
        after = [after]
    if after is not None:
        for a in after:
            if callable(a):
                after_names.append(a.__name__)
            elif type(a) is str:
                after_names.append(a)
            else:
                raise ValueError("after must be a list of callables or strings.")

    def decorator(func):
        # add wrapped flag to function
        func.__ba_wrapped__ = True

        # add before and after names to function
        func.__ba_before__ = before_names
        func.__ba_after__ = after_names

        # add include_base flag to function
        func.__ba_include_base__ = include_base

        # add include_inherited flag to function
        func.__ba_include_inherited__ = include_inherited

        # check if function is a class method
        if "." not in func.__qualname__:
            @wraps(func)
            def _module_wrap(*args, **kwargs):
                # get attrs from calling function
                attrs = inspect.currentframe().f_back.f_locals

                before_methods = _get_methods(before_names, attrs)
                after_methods = _get_methods(after_names, attrs)

                # get signatures
                func_signature, before_method_signatures, after_method_signatures = _get_signatures(func, before_methods, after_methods)

                return _wrapper(*args,
                                func=func,
                                before_methods=before_methods,
                                after_methods=after_methods,
                                func_signature=func_signature,
                                before_method_signatures=before_method_signatures,
                                after_method_signatures=after_method_signatures,
                                **kwargs)

            return _module_wrap

        return func

    return decorator
