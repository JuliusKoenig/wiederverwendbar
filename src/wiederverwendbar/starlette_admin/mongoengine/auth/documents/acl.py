from typing import Any

from mongoengine import Document, ReferenceField, ListField, StringField, BooleanField
from starlette.requests import Request

from wiederverwendbar.mongoengine.fields.boolean_also_field import BooleanAlsoField


class AccessControlList(Document):
    meta = {"collection": "acl"}

    name: str = StringField(required=True, unique=True)
    users: list[Any] = ListField(ReferenceField("User"))
    allow_read: bool = BooleanField(required=True)
    read_specify: list[str] = ListField(StringField())
    allow_create: bool = BooleanAlsoField(required=True, also=allow_read, help_text="Lesen ist Voraussetzung für Erstellen")
    create_specify: list[str] = ListField(StringField())
    allow_update: bool = BooleanAlsoField(required=True, also=allow_create, help_text="Erstellen ist Voraussetzung für Aktualisieren")
    edit_specify: list[str] = ListField(StringField())
    allow_delete: bool = BooleanAlsoField(required=True, also=allow_read, help_text="Lesen ist Voraussetzung für Löschen")
    delete_specify: list[str] = ListField(StringField())

    async def __admin_repr__(self, request: Request):
        return f"{self.name})"

