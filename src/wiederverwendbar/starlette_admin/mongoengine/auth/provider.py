from datetime import datetime
from typing import Optional, Sequence

from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminConfig, AdminUser, AuthProvider
from starlette_admin.exceptions import FormValidationError, LoginFailed
from wiederverwendbar.functions.eval import eval_value

from wiederverwendbar.starlette_admin.mongoengine.auth.documents.session import Session
from wiederverwendbar.starlette_admin.mongoengine.auth.documents.user import User
from wiederverwendbar.starlette_admin.mongoengine.helper import get_grid_fs_url
from wiederverwendbar.starlette_admin.settings import AuthAdminSettings


class MongoengineAdminAuthProvider(AuthProvider):
    def __init__(
            self,
            login_path: str = "/login",
            logout_path: str = "/logout",
            avatar_path: str = "/avatar",
            allow_paths: Optional[Sequence[str]] = None,
            allow_routes: Optional[Sequence[str]] = None,
            session_document_cls: Optional[type[Session]] = None,
            user_document_cls: Optional[type[User]] = None) -> None:

        # set avatar path
        self.avatar_path = avatar_path

        super().__init__(login_path=login_path, logout_path=logout_path, allow_paths=allow_paths, allow_routes=allow_routes)

        # Set default values
        self.session_document_cls = session_document_cls or Session
        self.user_document_cls = user_document_cls or User

    async def login(
            self,
            username: str,
            password: str,
            remember_me: bool,
            request: Request,
            response: Response,
    ) -> Response:
        # get settings
        settings = AuthAdminSettings.from_request(request=request)

        # get user from database
        user = self.user_document_cls.objects(username=username).first()
        if user is None:
            if settings.admin_debug:
                raise FormValidationError({"username": "User not found!"})
            raise LoginFailed("Invalid username or password!")

        # check if user password is set
        if user.password is None:
            if not settings.admin_user_allows_empty_password_login:
                if settings.admin_debug:
                    raise FormValidationError({"password": "Password is not set for this user!"})
                raise LoginFailed("Invalid username or password!")
        else:
            # validate password
            if not user.password.verify_password(password):
                if settings.admin_debug:
                    raise FormValidationError({"password": "Invalid password!"})
                raise LoginFailed("Invalid username or password!")

        # check if user have already a session
        if settings.admin_session_only_one:
            session = self.session_document_cls.objects(user=user).first()
            if session is not None:
                session.delete()

        # create new session
        session: Session = user.create_session_from_request(request=request)

        # save session id in session
        request.session.update({"session_id": str(session.id)})

        return response

    async def is_authenticated(self, request) -> bool:
        # get session
        session = self.session_document_cls.get_session_from_request(request)
        if session is None:
            return False

        # update user-agent
        session.user_agent = request.headers.get("User-Agent", "")

        # update last access
        session.last_access = datetime.now()

        # save session
        session.save()

        # save session in request state
        request.state.session = session

        return True

    def get_admin_config(self, request: Request) -> AdminConfig:
        # get settings
        settings = AuthAdminSettings.from_request(request=request)

        # get session
        if not hasattr(request.state, "session"):
            return AdminConfig(app_title=settings.admin_title, logo_url=settings.admin_logo_url)
        session = request.state.session

        # Update app title according to current_user
        custom_app_title = eval_value("Admin app title", settings.admin_user_app_title, session=session)

        # Update logo url according to current_user
        custom_logo_url = settings.admin_logo_url
        if session.user.company_logo is not None:
            custom_logo_url = str(request.url_for(settings.admin_route_name,
                                                  path=str(settings.admin_static_company_logo_dir / session.user.company_logo).replace("\\", "/")))

        return AdminConfig(app_title=custom_app_title, logo_url=custom_logo_url)

    def get_admin_user(self, request: Request) -> AdminUser:
        # get session
        if not hasattr(request.state, "session"):
            return AdminUser(username="")
        session = request.state.session

        # get avatar url
        avatar_url = get_grid_fs_url(session.user.avatar, request=request)

        return AdminUser(username=session.user.username, photo_url=avatar_url)

    async def logout(self, request: Request, response: Response) -> Response:
        #
        session = self.session_document_cls.get_session_from_request(request)
        if session is None:
            raise LoginFailed("Invalid session!")

        # delete session
        session.delete()

        # clear session
        request.session.clear()

        return response
