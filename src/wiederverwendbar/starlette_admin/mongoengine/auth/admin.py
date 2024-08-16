import logging
import string
import warnings
from typing import Optional, Sequence, Tuple, Any, Union

from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

from starlette_admin.contrib.mongoengine import Admin
from starlette_admin.i18n import I18nConfig
from starlette_admin.views import CustomView, DropDown, Link, BaseModelView, BaseView
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
    static_files_packages = [("wiederverwendbar", "starlette_admin/mongoengine/auth/statics")]

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
                                                          reference_loader=self.acl_reference_loader,
                                                          fields_loader=self.acl_fields_loader,
                                                          actions_loader=self.acl_actions_loader)

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
            if not self.user_document.objects(username=settings.admin_superuser_username, admin=True).first():
                if settings.admin_superuser_auto_create:
                    # create superuser
                    logger.info(f"Creating superuser with username '{settings.admin_superuser_username}' and password '{settings.admin_superuser_username}'")
                    superuser = self.user_document(admin=True, username=settings.admin_superuser_username)
                    superuser.password = settings.admin_superuser_username
                    superuser.save()
                else:
                    warnings.warn(f"Superuser with username '{settings.admin_superuser_username}' does not exist!", UserWarning)

        # disable jinja2 cache - ToDo: i don't know, but without disabling the cache, i have problems with dynamic list loaders
        self.templates.env.cache = None

    @property
    def _all_views(self) -> list[BaseView]:
        all_views: list[BaseView] = []

        def iterate_through_all_views(views: list):
            for view in views:
                if isinstance(view, DropDown):
                    iterate_through_all_views(view.views)
                elif isinstance(view, CustomView):
                    all_views.append(view)
                elif isinstance(view, Link):
                    all_views.append(view)
                elif isinstance(view, BaseModelView):
                    all_views.append(view)
                else:
                    raise ValueError(f"Unknown view type: {type(view)}")

        iterate_through_all_views(self._views)

        return all_views

    @property
    def _view_identity_mapping(self) -> dict[BaseView, str]:
        view_identity_mapping = {}
        for view in self._all_views:
            # get identity
            if getattr(view, "identity", "") != "" and getattr(view, "identity", None) is not None:
                _identity = getattr(view, "identity")
            elif getattr(view, "name", "") != "" and getattr(view, "name", None) is not None:
                _identity = getattr(view, "name")
            else:
                _identity = view.__class__.__name__

            # convert identity to snake_case and remove special characters
            identity = ""
            for c in _identity:
                if c in string.ascii_lowercase:
                    identity += c
                elif c in string.ascii_uppercase + string.digits:
                    if identity != "":
                        identity += "_"
                    identity += c.lower()
                else:
                    if identity != "":
                        identity += "_"

            # check if identity is already used
            if identity in view_identity_mapping.values():
                raise ValueError(f"Identity '{identity}' is already used by '{[k for k, v in view_identity_mapping.items() if v == identity][0]}'")

            view_identity_mapping[view] = identity

        return view_identity_mapping

    def setup_view(self, view: BaseView) -> None:
        super().setup_view(view)
        _ = self._view_identity_mapping

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

    def acl_reference_loader(self, request: Request) -> Sequence[Tuple[Any, str]]:
        references: list[tuple[str, str]] = [("all", "Alle")]

        for view, identity in self._view_identity_mapping.items():
            if isinstance(view, CustomView):
                references.append((f"view.{identity}", f"Ansicht {view.label}"))
            elif isinstance(view, Link):
                references.append((f"link.{identity}", f"Link {view.label}"))
            elif isinstance(view, BaseModelView):
                references.append((f"object.{identity}", f"Objekt {view.label}"))

        return references

    def acl_fields_loader(self, request: Request) -> Sequence[Tuple[Any, str]]:
        fields: list[tuple[str, str]] = []

        for view, identity in self._view_identity_mapping.items():
            if isinstance(view, BaseModelView):
                # skip if view is self.acl_view
                if view == self.acl_view:
                    continue

                # add fields to fields
                for field in view.fields:
                    # skip if field is id
                    if field.name == "id":
                        continue
                    # skip if field is not excluded from list
                    if not field.exclude_from_list:
                        continue
                    fields.append((f"object.{identity}.{field.name}", f"{field.label}"))

        return fields

    def acl_actions_loader(self, request: Request) -> Sequence[Tuple[Any, str]]:
        actions: list[tuple[str, str]] = []

        for view, identity in self._view_identity_mapping.items():
            if isinstance(view, BaseModelView):
                # add actions to actions
                for action in view.actions:
                    # skip delete action
                    if action == "delete":
                        continue
                    actions.append((f"object.{identity}.{action}", f"{action}"))

        return actions
