from datetime import datetime
from typing import Optional, Any

from mongoengine import Document, signals, ValidationError, StringField, DateTimeField, EmbeddedDocumentField, ReferenceField, ListField, ImageField, ImageGridFsProxy, BooleanField
from starlette.requests import Request

from wiederverwendbar.mongoengine.security.hashed_password import HashedPasswordDocument
from wiederverwendbar.starlette_admin.settings import AuthAdminSettings


class User(Document):
    class HashedPasswordDocument(HashedPasswordDocument):
        def __str__(self):
            return ""

    meta = {"collection": "user"}

    avatar: ImageGridFsProxy = ImageField(size=(100, 100))
    admin: bool = BooleanField(default=False, required=True)
    name: str = StringField(min_length=3, max_length=32, required=True, unique=True)
    groups: list[Any] = ListField(ReferenceField("Group"))
    password_doc: HashedPasswordDocument = EmbeddedDocumentField(HashedPasswordDocument)
    password_change_time: Optional[datetime] = DateTimeField()
    password_expiration_time: Optional[datetime] = DateTimeField()
    sessions: list[Any] = ListField(ReferenceField("Session"))
    company_logo: str = StringField()
    acls: list[Any] = ListField(ReferenceField("AccessControlList"))

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        changed_fields = getattr(document, "_changed_fields", [])

        # check if admin user is removed
        if "admin" in changed_fields:
            if not document.admin:
                # check this the last admin user
                if document.is_last_admin:
                    raise ValidationError(errors={"admin": "You can't remove the last admin user."})

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        # refresh groups
        # add user to all groups
        for group in document.groups:
            if document not in group.users:
                group.users.append(document)
                group.save()
        # remove user from all groups not in groups
        group_document_cls = getattr(document, "_fields")["groups"].field.document_type_obj
        for group in group_document_cls.objects(users__in=[document]):
            if group in document.groups:
                continue
            group.users.remove(document)
            group.save()

        # refresh acls
        # add user to all acls
        for acl in document.acls:
            if document not in acl.users:
                acl.users.append(document)
                acl.save()
        # remove user from all acls not in acls
        acl_document_cls = getattr(document, "_fields")["acls"].field.document_type_obj
        for acl in acl_document_cls.objects(users__in=[document]):
            if acl in document.acls:
                continue
            acl.users.remove(document)
            acl.save()

    @classmethod
    def pre_delete(cls, sender, document, **kwargs):
        # check if admin user is removed
        if document.admin:
            # check this the last admin user
            if document.is_last_admin:
                raise ValidationError(errors={"admin": "You can't remove the last admin user."})

    @classmethod
    def post_delete(cls, sender, document, **kwargs):
        # delete all sessions with this user
        for session in document.sessions:
            session.delete()

        # remove user from all groups
        for group in document.groups:
            group.users.remove(document)
            group.save()

        # remove user from all acls
        for acl in document.acls:
            acl.users.remove(document)
            acl.save()

    async def __admin_repr__(self, request: Request):
        return f"{self.name}"

    @property
    def is_last_admin(self) -> bool:
        return User.objects(admin=True).count() == 1

    @property
    def password(self) -> HashedPasswordDocument:
        return self.password_doc

    @password.setter
    def password(self, value: str) -> None:
        if value is None or value == "":
            return

        # set password
        self.password_doc = self.HashedPasswordDocument.hash_password(value)

        # set password change time
        self.password_change_time = datetime.now()

        # reset password expiration time
        if self.password_expiration_time is not None:
            if self.password_change_time > self.password_expiration_time:
                self.password_expiration_time = None

    def create_session_from_request(self, request: Request) -> Any:
        # get settings
        settings = AuthAdminSettings.from_request(request=request)

        # get user-agent
        user_agent = request.headers.get("User-Agent", "")

        session_document_cls = getattr(self, "_fields")["sessions"].field.document_type_obj

        session = session_document_cls(user=self,
                                       app_name=settings.admin_name,
                                       user_agent=user_agent,
                                       last_access=datetime.now())
        session.save()
        self.sessions.append(session)
        self.save()

        return session


signals.pre_save.connect(User.pre_save, sender=User)
signals.post_save.connect(User.post_save, sender=User)
signals.pre_delete.connect(User.pre_delete, sender=User)
signals.post_delete.connect(User.post_delete, sender=User)
