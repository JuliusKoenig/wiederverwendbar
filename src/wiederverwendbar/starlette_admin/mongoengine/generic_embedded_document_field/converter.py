from typing import Any

import mongoengine as me
import starlette_admin as sa
from starlette_admin.contrib.mongoengine.converters import ModelConverter, converts

from wiederverwendbar.starlette_admin.mongoengine.generic_embedded_document_field.field import GenericEmbeddedDocumentField


class Converter(ModelConverter):
    @converts(me.GenericEmbeddedDocumentField)
    def conv_generic_embedded_document_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        common = self._field_common(*args, **kwargs)
        field = kwargs["field"]
        if field.choices is None:
            raise ValueError("GenericEmbeddedDocumentField requires embedded_docs")
        embedded_doc_name_mapping = {}
        embedded_doc_fields = {}
        for doc in field.choices:
            if not issubclass(doc, me.EmbeddedDocument):
                raise ValueError(f"{doc} is not a subclass of EmbeddedDocument")
            doc_meta = getattr(doc, "_meta", {})
            name = doc_meta.get("name", doc.__name__)
            embedded_doc_name_mapping[name] = doc
            doc_fields = []
            for _field in getattr(doc, "_fields_ordered"):
                kwargs["field"] = getattr(doc, _field)
                doc_fields.append(self.convert(*args, **kwargs))
            embedded_doc_fields[name] = doc_fields
        return GenericEmbeddedDocumentField(**common, embedded_doc_fields=embedded_doc_fields, embedded_doc_name_mapping=embedded_doc_name_mapping)
