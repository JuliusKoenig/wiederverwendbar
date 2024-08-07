from datetime import datetime
from typing import Optional, Any

from mongoengine import Document, StringField, DateTimeField, EmbeddedDocumentField, ReferenceField, ListField, ImageField, ValidationError, ImageGridFsProxy
from starlette.requests import Request

from wiederverwendbar.mongoengine.security.hashed_password import HashedPasswordDocument
from wiederverwendbar.starlette_admin.settings import AuthAdminSettings


class User(Document):
    meta = {"collection": "user"}

    username: str = StringField(min_length=3, max_length=32, required=True, unique=True)
    password_doc: HashedPasswordDocument = EmbeddedDocumentField(HashedPasswordDocument)
    password_new_field: Optional[str] = StringField()
    password_new_repeat_field: Optional[str] = StringField()
    password_change_time: Optional[datetime] = DateTimeField()
    password_expiration_time: Optional[datetime] = DateTimeField()
    sessions: list[Any] = ListField(ReferenceField("Session"))
    avatar: ImageGridFsProxy = ImageField(size=(100, 100))
    company_logo: str = StringField()

    def __init__(self, *args, **values):
        super().__init__(*args, **values)

        # cleanup sessions they don't exist anymore
        sessions = []
        for session in self.sessions:
            if type(session) is not self.session_document_cls:
                continue
            sessions.append(session)
        if len(sessions) != len(self.sessions):
            self.sessions = sessions
            self.save()

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
        if self.password_new_field:
            if self.password_new_field != self.password_new_repeat_field:
                raise ValidationError(errors={"password_new_field": "The new password does not match the repeated password.",
                                              "password_new_repeat_field": "The repeated password does not match the new password."})
            self.password = self.password_new_field

            if self.password_expiration_time is not None:
                if self.password_change_time > self.password_expiration_time:
                    self.password_expiration_time = None
        self.password_new_field = None
        self.password_new_repeat_field = None

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
        self.password_change_time = datetime.now()

    @property
    def session_document_cls(self) -> type[Any]:
        return getattr(self, "_fields")["sessions"].field.document_type_obj

    def create_session_from_request(self, request: Request) -> Any:
        # get settings
        settings = AuthAdminSettings.from_request(request=request)

        # get user-agent
        user_agent = request.headers.get("User-Agent", "")

        session = self.session_document_cls(user=self,
                                            app_name=settings.admin_name,
                                            user_agent=user_agent,
                                            last_access=datetime.now())
        session.save()
        self.sessions.append(session)
        self.save()

        return session
