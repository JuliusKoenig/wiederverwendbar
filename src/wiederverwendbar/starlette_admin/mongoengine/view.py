from typing import Any, Dict, Type, Optional
import mongoengine as me

from starlette.requests import Request
from starlette_admin import action
from starlette_admin import RequestAction
from starlette_admin.contrib.mongoengine import ModelView as BaseModelView
from starlette_admin.contrib.mongoengine.converters import BaseMongoEngineModelConverter

from wiederverwendbar.starlette_admin.mongoengine.generic_embedded_document_field.view import GenericEmbeddedDocumentView
from wiederverwendbar.starlette_admin.mongoengine.converter import MongoengineConverter


class FixedModelView(BaseModelView):
    async def serialize(
            self,
            obj: Any,
            request: Request,
            action: RequestAction,
            include_relationships: bool = True,
            include_select2: bool = False,
    ) -> Dict[str, Any]:
        result = await super().serialize(obj, request, action, include_relationships, include_select2)
        result["id"] = str(result["id"])
        return result


class MongoengineModelView(FixedModelView, GenericEmbeddedDocumentView):
    def __init__(
            self,
            document: Type[me.Document],
            icon: Optional[str] = None,
            name: Optional[str] = None,
            label: Optional[str] = None,
            identity: Optional[str] = None,
            converter: Optional[BaseMongoEngineModelConverter] = None,
    ):
        super().__init__(document=document, icon=icon, name=name, label=label, identity=identity, converter=converter or MongoengineConverter())
