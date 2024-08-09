from typing import Union, Any, Optional

from mongoengine import BooleanField

from wiederverwendbar.mongoengine.fields.with_instance_field import WithInstanceField


class BooleanAlsoField(WithInstanceField):
    def __init__(self, also: Union[str, Any] = None, **kwargs):
        super().__init__(**kwargs)
        self.also: BooleanField = also

    def _set_owner_document(self, owner_document):
        super()._set_owner_document(owner_document)
        if type(self.also) is str:
            self.also = getattr(self.owner_document, self.also)
        if self.also is not None and not (isinstance(self.also, BooleanField) or isinstance(self.also, BooleanAlsoField)):
            raise ValueError("The field 'also' must be of type 'BooleanField'.")

    def validate(self, value, clean=True):
        # validate value
        if not isinstance(value, bool):
            self.error("BooleanField only accepts boolean values")

        # skip false values
        if not value:
            return

        # check if also field is set
        if self.also is None:
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
