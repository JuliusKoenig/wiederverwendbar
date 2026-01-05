from typing import Any

import mongoengine as me
import starlette_admin as sa
from starlette_admin.contrib.mongoengine.converters import ModelConverter, converts
from starlette_admin.helpers import slugify_class_name

from wiederverwendbar.starlette_admin.mongoengine.generic_embedded_document_field.field import GenericEmbeddedDocumentField, ListField


class GenericEmbeddedConverter(ModelConverter):
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
                if _field.startswith("_"):
                    continue
                kwargs["field"] = getattr(doc, _field)
                doc_fields.append(self.convert(*args, **kwargs))
            embedded_doc_fields[name] = doc_fields
        return GenericEmbeddedDocumentField(**common, embedded_doc_fields=embedded_doc_fields, embedded_doc_name_mapping=embedded_doc_name_mapping)

    @converts(me.ListField, me.SortedListField)
    def conv_list_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        field = kwargs["field"]
        if field.field is None:
            raise ValueError(f'ListField "{field.name}" must have field specified')
        if isinstance(
                field.field,
                (me.ReferenceField, me.CachedReferenceField, me.LazyReferenceField),
        ):
            """To Many reference"""
            dtype = field.field.document_type_obj
            identity = slugify_class_name(
                dtype if isinstance(dtype, str) else dtype.__name__
            )
            return sa.HasMany(**self._field_common(*args, **kwargs), identity=identity)
        field.field.name = field.name
        kwargs["field"] = field.field
        if isinstance(field.field, (me.DictField, me.MapField)):
            return self.convert(*args, **kwargs)
        if isinstance(field.field, me.EnumField):
            admin_field = self.convert(*args, **kwargs)
            admin_field.multiple = True  # type: ignore [attr-defined]
            return admin_field
        return ListField(self.convert(*args, **kwargs), required=field.required)
