from typing import Any

from mongoengine import Document, signals, ReferenceField, ListField, StringField, BooleanField, DictField
from starlette.requests import Request

from wiederverwendbar.mongoengine.fields.boolean_also_field import BooleanAlsoField


class AccessControlList(Document):
    meta = {"collection": "auth.acl"}

    name: str = StringField(required=True, unique=True)
    users: list[Any] = ListField(ReferenceField("User"))
    groups: list[Any] = ListField(ReferenceField("Group"))
    object: str = StringField(required=True)
    query_filter: dict = DictField()
    allow_detail: bool = BooleanField()
    allow_create: bool = BooleanAlsoField(also=allow_detail)
    allow_update: bool = BooleanAlsoField(also=allow_create)
    specify_fields: list[str] = ListField(StringField())
    allow_delete: bool = BooleanField()
    allow_execute: bool = BooleanField()
    specify_actions: list[str] = ListField(StringField())

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        # refresh users
        # add acl to all users
        for user in document.users:
            if document not in user.acls:
                user.acls.append(document)
                user.save()
        # remove acl from all users not in users
        user_document_cls = getattr(document, "_fields")["users"].field.document_type_obj
        for user in user_document_cls.objects(acls__in=[document]):
            if user in document.users:
                continue
            user.acls.remove(document)
            user.save()

        # refresh groups
        # add acl to all groups
        for group in document.groups:
            if document not in group.acls:
                group.acls.append(document)
                group.save()
        # remove acl from all groups not in groups
        group_document_cls = getattr(document, "_fields")["groups"].field.document_type_obj
        for group in group_document_cls.objects(acls__in=[document]):
            if group in document.groups:
                continue
            group.acls.remove(document)
            group.save()

    @classmethod
    def post_delete(cls, sender, document, **kwargs):
        # remove acl from all users
        for user in document.users:
            user.acls.remove(document)
            user.save()

        # remove acl from all groups
        for group in document.groups:
            group.acls.remove(document)
            group.save()

    async def __admin_repr__(self, request: Request):
        return f"{self.name}"


signals.post_save.connect(AccessControlList.post_save, sender=AccessControlList)
signals.post_delete.connect(AccessControlList.post_delete, sender=AccessControlList)
