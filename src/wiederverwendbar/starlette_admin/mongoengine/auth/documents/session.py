from datetime import datetime, timedelta
from typing import Optional

from mongoengine import Document, ReferenceField, DateTimeField, StringField, CASCADE
from starlette.requests import Request

from wiederverwendbar.starlette_admin.mongoengine.auth.documents.user import User
from wiederverwendbar.starlette_admin.settings import AuthAdminSettings


class Session(Document):
    meta = {"collection": "session"}

    user: User = ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    app_name: str = StringField(regex=r"^[a-zA-Z0-9_-]+$", required=True)
    user_agent: str = StringField(default="")
    created: datetime = DateTimeField(default=datetime.now, required=True)
    last_access: datetime = DateTimeField()

    async def __admin_repr__(self, request: Request):
        return f"{await self.user.__admin_repr__(request)} - {self.id})"

    @classmethod
    def get_session_from_request(cls, request: Request) -> Optional["Session"]:
        # get settings
        settings = AuthAdminSettings.from_request(request=request)

        # expire sessions
        now = datetime.now()
        for session in cls.objects(app_name=settings.admin_name):
            expired = False
            if settings.admin_session_max_age is not None:
                if session.last_access + timedelta(seconds=settings.admin_session_max_age) < now:
                    expired = True
            if settings.admin_session_absolute_max_age is not None:
                if session.created + timedelta(seconds=settings.admin_session_absolute_max_age) < now:
                    expired = True
            if expired:
                session.delete()

        # get session id from session
        session_id = request.session.get("session_id", None)
        if session_id is None:
            return None

        # get session from database
        session = cls.objects(id=session_id, app_name=settings.admin_name).first()
        if session is None:
            return None

        return session
