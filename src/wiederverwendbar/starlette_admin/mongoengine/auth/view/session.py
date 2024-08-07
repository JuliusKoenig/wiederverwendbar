from typing import Type, Optional

from starlette.requests import Request
from starlette_admin.contrib.mongoengine.converters import BaseMongoEngineModelConverter

from wiederverwendbar.starlette_admin.mongoengine.auth.document.session import Session
from wiederverwendbar.starlette_admin.mongoengine.view import MongoengineModelView


class SessionView(MongoengineModelView):
    exclude_fields_from_list = []
    exclude_fields_from_detail = []
    exclude_fields_from_create = []
    exclude_fields_from_edit = []

    def __init__(
            self,
            document: Type[Session],
            icon: Optional[str] = None,
            name: Optional[str] = None,
            label: Optional[str] = None,
            identity: Optional[str] = None,
            converter: Optional[BaseMongoEngineModelConverter] = None,
    ):
        # set default values
        document = document or Session
        icon = icon or "fa-solid fa-list"
        name = name or "Session"
        label = label or "Sitzung"

        super().__init__(document=document,
                         icon=icon,
                         name=name,
                         label=label,
                         identity=identity,
                         converter=converter)
        for field in self.fields:
            if field.name == "user":
                field.label = "Benutzer"
            elif field.name == "created":
                field.label = "Erstellt"
            elif field.name == "last_access":
                field.label = "Letzter Zugriff"

    def can_create(self, request: Request) -> bool:
        return False

    def can_edit(self, request: Request) -> bool:
        return False
