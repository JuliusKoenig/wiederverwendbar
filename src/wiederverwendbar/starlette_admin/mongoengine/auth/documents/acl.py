from typing import Any

from mongoengine import Document, ReferenceField, ListField, StringField, BooleanField, DictField
from starlette.requests import Request

from wiederverwendbar.mongoengine.fields.boolean_also_field import BooleanAlsoField


class AccessControlList(Document):
    meta = {"collection": "acl"}

    name: str = StringField(required=True, unique=True)
    users: list[Any] = ListField(ReferenceField("User"))
    object: str = StringField(required=True)
    query_filter: dict = DictField()
    allow_detail: bool = BooleanField()
    allow_create: bool = BooleanAlsoField(also=allow_detail)
    allow_update: bool = BooleanAlsoField(also=allow_create)
    specify_fields: list[str] = ListField(StringField())
    allow_delete: bool = BooleanField()
    allow_execute: bool = BooleanField()
    specify_actions: list[str] = ListField(StringField())

    async def __admin_repr__(self, request: Request):
        return f"{self.name} - (object={self.object})"

