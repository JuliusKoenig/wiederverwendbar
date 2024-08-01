from datetime import datetime
from typing import Optional

from mongoengine import Document, StringField, DateTimeField, EmbeddedDocumentField, ReferenceField, ListField, ImageField, ValidationError, PULL, ImageGridFsProxy
from starlette.requests import Request

from wiederverwendbar.mongoengine.security.hashed_password import HashedPasswordDocument
from wiederverwendbar.starlette_admin.settings import AuthAdminSettings
from wiederverwendbar.starlette_admin.mongoengine.auth.document.session import Session


class User(Document):
    meta = {"collection": "user"}

    username: str = StringField(min_length=3, max_length=32, required=True, unique=True)
    password_doc: HashedPasswordDocument = EmbeddedDocumentField(HashedPasswordDocument)
    password_new_field: Optional[str] = StringField()
    password_new_repeat_field: Optional[str] = StringField()
    password_change_time: Optional[datetime] = DateTimeField()
    password_expiration_time: Optional[datetime] = DateTimeField()
    sessions: list[Session] = ListField(ReferenceField(Session, reverse_delete_rule=PULL))
    avatar: ImageGridFsProxy = ImageField()
    company_logo: str = StringField()

    def save(
            self,
            force_insert=False,
            validate=True,
            clean=True,
            write_concern=None,
            cascade=None,
            cascade_kwargs=None,
            _refs=None,
            save_condition=None,
            signal_kwargs=None,
            **kwargs,
    ):
        changed_fields = getattr(self, "_changed_fields", [])

        if self.password_new_field and "password_new_field" in changed_fields:
            if self.password_new_field != self.password_new_repeat_field:
                raise ValidationError(errors={"password_new_field": "The new password does not match the repeated password.",
                                              "password_new_repeat_field": "The repeated password does not match the new password."})
            self.password = self.password_new_field
            self.password_new_field = None
            self.password_new_repeat_field = None
        if "password_doc" in changed_fields:
            self.password_change_time = None if self.password is None else datetime.now()
        if "password_change_time" in changed_fields:
            if self.password_change_time is None:
                self.password_expiration_time = None
            else:
                if not self.password_expiration_time:
                    if self.password_change_time > self.password_expiration_time:
                        self.password_expiration_time = None

        return super().save(
            force_insert=force_insert,
            validate=validate,
            clean=clean,
            write_concern=write_concern,
            cascade=cascade,
            cascade_kwargs=cascade_kwargs,
            _refs=_refs,
            save_condition=save_condition,
            signal_kwargs=signal_kwargs,
            **kwargs,
        )

    async def __admin_repr__(self, request: Request):
        return f"{self.username}"

    @property
    def password(self) -> HashedPasswordDocument:
        return self.password_doc

    @password.setter
    def password(self, value: str) -> None:
        self.password_doc = HashedPasswordDocument.hash_password(value)

    def create_session_from_request(self, request: Request) -> Session:
        # get settings
        settings = AuthAdminSettings.from_request(request=request)

        # get user-agent
        user_agent = request.headers.get("User-Agent", "")

        session = Session(user=self,
                          app_name=settings.admin_name,
                          user_agent=user_agent,
                          last_access=datetime.now())
        session.save()
        self.sessions.append(session)
        self.save()

        return session
