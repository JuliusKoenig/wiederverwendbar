from typing import Any

from mongoengine import Document, ReferenceField, ListField, StringField, BooleanField, DictField
from starlette.requests import Request

from wiederverwendbar.mongoengine.fields.boolean_also_field import BooleanAlsoField


class AccessControlList(Document):
    meta = {"collection": "acl"}

    name: str = StringField(required=True, unique=True)
    users: list[Any] = ListField(ReferenceField("User"))
    object: str = StringField(required=True, help_text="Objekt, für das die Berechtigung gilt.")
    query_filter: dict = DictField(help_text="Filter für die Berechtigung. Muss ein gültiger MongoDB Query sein.")
    allow_read: bool = BooleanField(required=True, help_text="Lesen ist die grundlegende Berechtigung.")
    allow_create: bool = BooleanAlsoField(required=True, also=allow_read, help_text="Lesen ist Voraussetzung für Erstellen.")
    allow_update: bool = BooleanAlsoField(required=True, also=allow_create, help_text="Erstellen ist Voraussetzung für Aktualisieren.")
    allow_delete: bool = BooleanAlsoField(required=True, also=allow_read, help_text="Lesen ist Voraussetzung für Löschen.")
    allow_execute: bool = BooleanAlsoField(required=True, also=allow_read, help_text="Lesen ist Voraussetzung für Ausführen.")
    specify_fields: list[str] = ListField(StringField(), help_text="Schränke die Felder ein, für die die Berechtigung gilt. "
                                                                   "Felder, die in der List-View angezeigt werden, sind immer erlaubt.")
    specify_actions: list[str] = ListField(StringField(), help_text="Schränke die Aktionen ein, für die die Berechtigung gilt.")

    async def __admin_repr__(self, request: Request):
        return f"{self.name})"

