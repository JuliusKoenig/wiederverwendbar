from pydantic import BaseModel
from pydantic import Field as BaseField


# noinspection PyPep8Naming
def Field(*args, secret: bool = False, **kwargs) -> BaseField:
    """This method does the same as :py:class:`pydantic.Field`, but adds the possibility to hide the value."""

    if secret:
        kwargs.update(secret=True)

    return BaseField(*args, **kwargs)


class PrintableSettings(BaseModel):
    """
    Base class for settings that can be printed.
    Secrets are hidden.
    """

    def __repr_args__(self):
        for k, v in super().__repr_args__():
            field = self.model_fields.get(k)
            json_scheme_extra = field.json_schema_extra if field.json_schema_extra is not None else {}
            secret = json_scheme_extra.get("secret", False)
            if secret:
                yield k, "********"
            else:
                yield k, v
