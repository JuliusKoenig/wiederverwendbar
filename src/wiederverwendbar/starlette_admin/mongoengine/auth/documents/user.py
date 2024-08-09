from datetime import datetime
from typing import Optional, Any

from mongoengine import Document, StringField, DateTimeField, EmbeddedDocumentField, ReferenceField, ListField, ImageField, ImageGridFsProxy
from starlette.requests import Request

from wiederverwendbar.mongoengine.security.hashed_password import HashedPasswordDocument
from wiederverwendbar.starlette_admin.settings import AuthAdminSettings


class User(Document):
    class HashedPasswordDocument(HashedPasswordDocument):
        def __str__(self):
            return ""

    meta = {"collection": "user"}

    username: str = StringField(min_length=3, max_length=32, required=True, unique=True)
    password_doc: HashedPasswordDocument = EmbeddedDocumentField(HashedPasswordDocument)
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

    async def __admin_repr__(self, request: Request):
        return f"{self.username}"

    @property
    def password(self) -> HashedPasswordDocument:
        return self.password_doc

    @password.setter
    def password(self, value: str) -> None:
        # set password
        self.password_doc = HashedPasswordDocument.hash_password(value)

        # set password change time
        self.password_change_time = datetime.now()

        # reset password expiration time
        if self.password_expiration_time is not None:
            if self.password_change_time > self.password_expiration_time:
                self.password_expiration_time = None

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
