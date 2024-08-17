from datetime import datetime, timedelta
from typing import Optional

from mongoengine import Document, signals, DoesNotExist, ReferenceField, DateTimeField, StringField
from starlette.requests import Request

from wiederverwendbar.starlette_admin.mongoengine.auth.documents.acl import AccessControlList
from wiederverwendbar.starlette_admin.mongoengine.auth.documents.user import User
from wiederverwendbar.starlette_admin.settings import AuthAdminSettings


class Session(Document):
    meta = {"collection": "auth.session"}

    user: User = ReferenceField(User, required=True)
    app_name: str = StringField(regex=r"^[a-zA-Z0-9_-]+$", required=True)
    user_agent: str = StringField(default="")
    created: datetime = DateTimeField(default=datetime.now, required=True)
    last_access: datetime = DateTimeField()

    @classmethod
    def post_delete(cls, sender, document, **kwargs):
        # delete session from user
        try:
            _ = document.user
        except DoesNotExist:
            return
        document.user.sessions.remove(document)
        document.user.save()

    async def __admin_repr__(self, request: Request):
        return f"{self.id} - (username={self.user.name})"

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

    def get_acls(self, object_filter: Optional[str] = None) -> list[AccessControlList]:
        return self.user.get_acls(object_filter=object_filter)


signals.post_delete.connect(Session.post_delete, sender=Session)
