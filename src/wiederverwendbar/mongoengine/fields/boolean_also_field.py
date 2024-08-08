from typing import Union, Any, Optional

from mongoengine import BooleanField

from wiederverwendbar.mongoengine.fields.with_instance_field import WithInstanceField


class BooleanAlsoField(WithInstanceField):
    def __init__(self, also: Union[str, Any] = None, only_on: Optional[bool] = None, **kwargs):
        super().__init__(**kwargs)
        self.also: BooleanField = also
        self.only_on = only_on

    def _set_owner_document(self, owner_document):
        super()._set_owner_document(owner_document)
        if type(self.also) is str:
            self.also = getattr(self.owner_document, self.also)
        if self.also is not None and not isinstance(self.also, BooleanField):
            raise ValueError("The field 'also' must be of type 'BooleanField'.")

    def validate(self, value):
        # validate value
        if not isinstance(value, bool):
            self.error("BooleanField only accepts boolean values")

        # check if also field is set
        if self.also is None:
            return

        # check if only_on is set and value equals only_on
        if self.only_on is not None and value != self.only_on:
            return

        # get instance
        instance = self.get_instance()

        # set value of also field
        setattr(instance, self.also.name, value)

        # trigger validation of also field
        self.also.validate(value)

    def to_python(self, value):
        try:
            value = bool(value)
        except (ValueError, TypeError):
            pass
        return value
