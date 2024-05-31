from typing import Callable, Union


def find_class_method(bases, method_name) -> Union[Callable, None]:
    for base in bases:
        if hasattr(base, method_name):
            return getattr(base, method_name)
        for _bases in base.__bases__:
            if _bases is object:
                continue
            found = find_class_method(bases=_bases, method_name=method_name)
            if found is not None:
                return found
    return None
