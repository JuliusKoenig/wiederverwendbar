from typing import Any

import starlette_admin as sa
from starlette_admin.contrib.mongoengine.converters import ModelConverter, converts
from mongoengine import BooleanField as MongoengineBooleanField

from wiederverwendbar.mongoengine.fields.boolean_also_field import BooleanAlsoField as MongoengineBooleanAlsoField
from wiederverwendbar.starlette_admin.mongoengine.boolean_also_field.field import BooleanAlsoField as StarletteAdminBooleanAlsoField


class BooleanAlsoConverter(ModelConverter):
    @converts(MongoengineBooleanField, MongoengineBooleanAlsoField)
    def conv_boolean_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        field = kwargs['field']
        also=""
        if isinstance(field, MongoengineBooleanAlsoField):
            also=field.also.name
        return StarletteAdminBooleanAlsoField(**self._field_common(*args, **kwargs), also=also)
