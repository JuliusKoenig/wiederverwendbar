from typing import Any

from mongoengine import Document, signals, StringField, ReferenceField, ListField
from starlette.requests import Request

from wiederverwendbar.mongoengine.security.hashed_password import HashedPasswordDocument


class Group(Document):
    class HashedPasswordDocument(HashedPasswordDocument):
        def __str__(self):
            return ""

    meta = {"collection": "group"}

    name: str = StringField(min_length=3, max_length=32, required=True, unique=True)
    company_logo: str = StringField()
    users: list[Any] = ListField(ReferenceField("User"))
    acls: list[Any] = ListField(ReferenceField("AccessControlList"))

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        # refresh users
        # add group to all users
        for user in document.users:
            if document not in user.groups:
                user.groups.append(document)
                user.save()
        # remove group from all users not in users
        user_document_cls = getattr(document, "_fields")["users"].field.document_type_obj
        for user in user_document_cls.objects(groups__in=[document]):
            if user in document.users:
                continue
            user.groups.remove(document)
            user.save()

        # refresh acls
        # add group to all acls
        for acl in document.acls:
            if document not in acl.groups:
                acl.groups.append(document)
                acl.save()
        # remove group from all acls not in acls
        acl_document_cls = getattr(document, "_fields")["acls"].field.document_type_obj
        for acl in acl_document_cls.objects(groups__in=[document]):
            if acl in document.acls:
                continue
            acl.groups.remove(document)
            acl.save()

    @classmethod
    def post_delete(cls, sender, document, **kwargs):
        # remove group from all users
        for user in document.users:
            user.groups.remove(document)
            user.save()

        # remove user from all acls
        for acl in document.acls:
            acl.groups.remove(document)
            acl.save()

    async def __admin_repr__(self, request: Request):
        return f"{self.name}"


signals.post_save.connect(Group.post_save, sender=Group)
signals.post_delete.connect(Group.post_delete, sender=Group)
