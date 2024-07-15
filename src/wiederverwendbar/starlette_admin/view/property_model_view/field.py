from typing import Callable, Type
from starlette_admin.fields import BaseField


def property_field(field: Type[BaseField], **kwargs):
    def decorator(fget: Callable):
        fget.__sa_field_type__ = field
        kwargs["name"] = fget.__name__
        fget.__sa_field_kwargs__ = kwargs
        p = property(fget)
        return p

    return decorator
