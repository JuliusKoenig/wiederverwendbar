from typing import Any

import mongoengine as me
import starlette_admin as sa
from starlette_admin.contrib.mongoengine.converters import ModelConverter, converts

from wiederverwendbar.starlette_admin.mongoengine.fixed_collection_field.field import CollectionField


class Converter(ModelConverter):
    @converts(me.EmbeddedDocumentField)
    def conv_embedded_document_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        field = kwargs["field"]
        document_type_obj: me.EmbeddedDocument = field.document_type
        _fields = []
        for _field in document_type_obj._fields_ordered:
            kwargs["field"] = getattr(document_type_obj, _field)
            _fields.append(self.convert(*args, **kwargs))
        return CollectionField(field.name, _fields, field.required)
