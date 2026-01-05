from copy import deepcopy
from typing import Dict, Any

from starlette.requests import Request
from starlette_admin.contrib.mongoengine.view import ModelView as BaseModelView

from wiederverwendbar.starlette_admin.mongoengine.generic_embedded_document_field.field import GenericEmbeddedDocumentField, ListField


class GenericEmbeddedDocumentView(BaseModelView):
    async def convert_generic_embedded_document(self, request: Request, data: Dict[str, Any], obj: Any) -> None:
        data = deepcopy(data)
        for field in self.fields:
            if isinstance(field, GenericEmbeddedDocumentField):
                value = data.get(field.name)
                if value is None:
                    continue
                value = await field.convert_generic_embedded_document(request, value)
                setattr(obj, field.name, value)
            elif isinstance(field, ListField) and isinstance(field.field, GenericEmbeddedDocumentField):
                for index, item in enumerate(data.get(field.name, [])):
                    value = await field.field.convert_generic_embedded_document(request, item)
                    data[field.name][index] = value
                setattr(obj, field.name, data[field.name])

    async def before_create(
            self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        await self.convert_generic_embedded_document(request, data, obj)

    async def before_edit(
            self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        await self.convert_generic_embedded_document(request, data, obj)
