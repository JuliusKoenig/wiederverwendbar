import logging
import warnings
from typing import Optional, Sequence, Tuple, Any, Union, Literal

from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

from starlette_admin.contrib.mongoengine import Admin
from starlette_admin.i18n import I18nConfig
from starlette_admin.views import CustomView, DropDown, Link, BaseModelView
from starlette_admin.auth import BaseAuthProvider

from wiederverwendbar.starlette_admin.admin import SettingsAdmin
from wiederverwendbar.starlette_admin.settings import AuthAdminSettings
from wiederverwendbar.starlette_admin.drop_down_icon_view.admin import DropDownIconViewAdmin
from wiederverwendbar.starlette_admin.mongoengine.auth.documents.acl import AccessControlList
from wiederverwendbar.starlette_admin.mongoengine.auth.views.acl import AccessControlListView
from wiederverwendbar.starlette_admin.mongoengine.auth.views.auth import AuthView
from wiederverwendbar.starlette_admin.mongoengine.boolean_also_field.admin import BooleanAlsoAdmin
from wiederverwendbar.starlette_admin.mongoengine.auth.provider import MongoengineAdminAuthProvider
from wiederverwendbar.starlette_admin.mongoengine.auth.documents.session import Session
from wiederverwendbar.starlette_admin.mongoengine.auth.views.session import SessionView
from wiederverwendbar.starlette_admin.mongoengine.auth.views.user import UserView
from wiederverwendbar.starlette_admin.mongoengine.auth.documents.user import User

logger = logging.getLogger(__name__)


class MongoengineAuthAdmin(SettingsAdmin, DropDownIconViewAdmin, BooleanAlsoAdmin, Admin):
    def __init__(
            self,
            title: Optional[str] = None,
            base_url: Optional[str] = None,
            route_name: Optional[str] = None,
            logo_url: Optional[str] = None,
            login_logo_url: Optional[str] = None,
            templates_dir: Optional[str] = None,
            statics_dir: Optional[str] = None,
            index_view: Optional[CustomView] = None,
            auth_view: Union[None, AuthView, bool] = None,
            user_document: Optional[type[User]] = None,
            user_view: Optional[UserView] = None,
            session_document: Optional[type[Session]] = None,
            session_view: Optional[SessionView] = None,
            acl_document: Optional[type[AccessControlList]] = None,
            acl_view: Optional[AccessControlListView] = None,
            auth_provider: Optional[BaseAuthProvider] = None,
            middlewares: Optional[Sequence[Middleware]] = None,
            session_middleware: Optional[type[SessionMiddleware]] = None,
            debug: Optional[bool] = None,
            i18n_config: Optional[I18nConfig] = None,
            favicon_url: Optional[str] = None,
            settings: Optional[AuthAdminSettings] = None
    ):
        # get settings from the settings class if not provided
        settings = settings or AuthAdminSettings()
        if not isinstance(settings, AuthAdminSettings):
            raise ValueError(f"settings must be an instance of {AuthAdminSettings.__name__}")

        # set middlewares
        middlewares = middlewares or []

        # set session middleware
        session_middleware = session_middleware or SessionMiddleware
        if not any(issubclass(middleware.cls, SessionMiddleware) for middleware in middlewares):
            middlewares.append(Middleware(session_middleware,  # noqa
                                          secret_key=settings.admin_session_secret_key,
                                          session_cookie=settings.admin_session_cookie,
                                          max_age=settings.admin_session_max_age,
                                          path=settings.admin_session_path,
                                          same_site=settings.admin_session_same_site.value,
                                          https_only=settings.admin_session_https_only,
                                          domain=settings.admin_session_domain))

        # set documents
        self.user_document = user_document or User
        self.session_document = session_document or Session
        self.acl_document = acl_document or AccessControlList

        # set views
        if auth_view is None:
            auth_view = AuthView()
        self.auth_view = auth_view
        self.user_view = user_view or UserView(document=self.user_document, company_logo_choices_loader=self.user_company_logo_files_loader)
        self.session_view = session_view or SessionView(document=self.session_document)
        self.acl_view = acl_view or AccessControlListView(document=self.acl_document,
                                                          read_specify_loader=lambda request: self._acl_specify_loader(request, mode="read"),
                                                          create_specify_loader=lambda request: self._acl_specify_loader(request, mode="create"),
                                                          edit_specify_loader=lambda request: self._acl_specify_loader(request, mode="edit"),
                                                          delete_specify_loader=lambda request: self._acl_specify_loader(request, mode="delete"))

        # set auth_provider
        if settings.admin_auth:
            auth_provider = auth_provider or MongoengineAdminAuthProvider(login_path=settings.admin_login_path,
                                                                          logout_path=settings.admin_logout_path,
                                                                          avatar_path=f"/{self.user_view.identity}/avatar",
                                                                          allow_routes=settings.admin_allow_routes,
                                                                          session_document_cls=session_document,
                                                                          user_document_cls=user_document)
        else:
            auth_provider = None
        self.auth_provider = auth_provider

        super().__init__(
            title=title,
            base_url=base_url,
            route_name=route_name,
            logo_url=logo_url,
            login_logo_url=login_logo_url,
            templates_dir=templates_dir,
            statics_dir=statics_dir,
            index_view=index_view,
            auth_provider=auth_provider,
            middlewares=middlewares,
            debug=debug,
            i18n_config=i18n_config,
            favicon_url=favicon_url,
            settings=settings,
        )

        # create views
        if self.auth_view:
            self.auth_view.views = [self.user_view, self.session_view, self.acl_view]
            self.add_view(self.auth_view)
        else:
            self.add_view(self.user_view)
            self.add_view(self.session_view)
            self.add_view(self.acl_view)

        # check if superuser is set
        if settings.admin_superuser_username is not None:
            # check if superuser exists
            if not self.user_document.objects(username=settings.admin_superuser_username).first():
                if settings.admin_superuser_auto_create:
                    # create superuser
                    logger.info(f"Creating superuser with username '{settings.admin_superuser_username}' and password '{settings.admin_superuser_username}'")
                    superuser = self.user_document(username=settings.admin_superuser_username)
                    superuser.password = settings.admin_superuser_username
                    superuser.save()
                else:
                    warnings.warn(f"Superuser with username '{settings.admin_superuser_username}' does not exist!", UserWarning)

    def user_company_logo_files_loader(self, request: Request) -> Sequence[Tuple[Any, str]]:
        if not self.settings.admin_static_company_logo_dir:
            return []
        company_logo_files = []
        for file in self.settings.admin_static_company_logo_dir.iterdir():
            if not file.is_file():
                continue
            if file.suffix not in self.settings.admin_company_logos_suffixes:
                continue
            company_logo_files.append((file.name, file.name))
        return company_logo_files

    def _acl_specify_loader(self, request: Request, mode: Literal["read", "create", "edit", "delete"]) -> Sequence[Tuple[Any, str]]:
        references: list[tuple[str, str]] = []

        def iterate_through_all_views(views: list, key_prefix: str = ""):
            if key_prefix != "":
                key_prefix += "."

            for view in views:
                if isinstance(view, DropDown):
                    iterate_through_all_views(view.views, key_prefix + view.label)
                elif isinstance(view, CustomView):
                    # skip if mode is "create", "edit" or "delete"
                    if mode in ["create", "edit", "delete"]:
                        continue
                    references.append((f"{key_prefix}{view.name}", f"Ansicht {view.label}"))
                elif isinstance(view, Link):
                    # skip if mode is "create", "edit" or "delete"
                    if mode in ["create", "edit", "delete"]:
                        continue
                    references.append((f"{key_prefix}{view.label}", f"Link {view.label}"))
                elif isinstance(view, BaseModelView):
                    # add model view to references
                    references.append((f"{key_prefix}{view.name}.*", f"Objekt {view.label}"))

                    # skip if view is self.acl_view
                    if view == self.acl_view:
                        continue

                    # skip if mode is "delete"
                    if mode == "delete":
                        continue

                    # add fields to references
                    for field in view.fields:
                        can = ["read", "create", "edit"]
                        # check is field excluded
                        if field.exclude_from_list and field.exclude_from_detail:
                            can.remove("read")
                        if field.exclude_from_create:
                            can.remove("create")
                        if field.exclude_from_edit:
                            can.remove("edit")
                        if mode not in can:
                            continue

                        references.append((f"{key_prefix}{view.name}.{field.name}", f"Objekt {view.label} - Feld {field.label}"))
                else:
                    raise ValueError(f"Unknown view type: {type(view)}")

        iterate_through_all_views(self._views)

        return references
