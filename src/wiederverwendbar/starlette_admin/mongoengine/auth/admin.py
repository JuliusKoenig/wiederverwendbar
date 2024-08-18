import logging
import string
import warnings
from typing import Optional, Sequence, Tuple, Any, Union

from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

from starlette_admin.contrib.mongoengine import Admin
from starlette_admin.i18n import I18nConfig
from starlette_admin.views import DropDown
from starlette_admin.auth import BaseAuthProvider

from wiederverwendbar.starlette_admin.admin import SettingsAdmin
from wiederverwendbar.starlette_admin.mongoengine.auth.views.base import BaseView
from wiederverwendbar.starlette_admin.mongoengine.auth.views.custom import CustomView
from wiederverwendbar.starlette_admin.mongoengine.auth.views.link import Link
from wiederverwendbar.starlette_admin.mongoengine.auth.views.model import ModelView
from wiederverwendbar.starlette_admin.settings import AuthAdminSettings
from wiederverwendbar.starlette_admin.drop_down_icon_view.admin import DropDownIconViewAdmin
from wiederverwendbar.starlette_admin.mongoengine.boolean_also_field.admin import BooleanAlsoAdmin
from wiederverwendbar.starlette_admin.mongoengine.auth.provider import MongoengineAdminAuthProvider
from wiederverwendbar.starlette_admin.mongoengine.auth.documents.acl import AccessControlList
from wiederverwendbar.starlette_admin.mongoengine.auth.documents.group import Group
from wiederverwendbar.starlette_admin.mongoengine.auth.documents.session import Session
from wiederverwendbar.starlette_admin.mongoengine.auth.documents.user import User
from wiederverwendbar.starlette_admin.mongoengine.auth.views.acl import AccessControlListView
from wiederverwendbar.starlette_admin.mongoengine.auth.views.auth import AuthView
from wiederverwendbar.starlette_admin.mongoengine.auth.views.group import GroupView
from wiederverwendbar.starlette_admin.mongoengine.auth.views.session import SessionView
from wiederverwendbar.starlette_admin.mongoengine.auth.views.user import UserView

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
            group_document: Optional[type[Group]] = None,
            group_view: Optional[GroupView] = None,
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
        self.acl_document = acl_document or AccessControlList
        self.group_document = group_document or Group
        self.session_document = session_document or Session
        self.user_document = user_document or User

        # set views
        self.acl_view = acl_view or AccessControlListView(document=self.acl_document,
                                                          reference_loader=self.acl_reference_loader,
                                                          fields_loader=self.acl_fields_loader,
                                                          actions_loader=self.acl_actions_loader)
        if auth_view is None:
            auth_view = AuthView()
        self.auth_view = auth_view
        self.group_view = group_view or GroupView(document=self.group_document, company_logo_choices_loader=self.company_logo_files_loader)
        self.session_view = session_view or SessionView(document=self.session_document)
        self.user_view = user_view or UserView(document=self.user_document, company_logo_choices_loader=self.company_logo_files_loader)

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
            self.auth_view.views = [self.user_view, self.group_view, self.session_view, self.acl_view]
            self.add_view(self.auth_view)
        else:
            self.add_view(self.user_view)
            self.add_view(self.group_view)
            self.add_view(self.session_view)
            self.add_view(self.acl_view)

        # check if superuser is set
        if settings.admin_superuser_name is not None:
            # check if superuser exists
            if not self.user_document.objects(name=settings.admin_superuser_name, admin=True).first():
                if settings.admin_superuser_auto_create:
                    # create superuser
                    logger.info(f"Creating superuser with username '{settings.admin_superuser_name}' and password '{settings.admin_superuser_name}'")
                    superuser = self.user_document(admin=True, name=settings.admin_superuser_name)
                    superuser.password = settings.admin_superuser_name
                    superuser.save()
                else:
                    warnings.warn(f"Superuser with username '{settings.admin_superuser_name}' does not exist!", UserWarning)

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
                elif isinstance(view, ModelView):
                    all_views.append(view)
                else:
                    raise ValueError(f"Unknown view type: {type(view)}")

        iterate_through_all_views(self._views)

        return all_views

    @property
    def view_identity_mapping(self) -> dict[BaseView, str]:
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

            if isinstance(view, CustomView):
                identity = f"view.{identity}"
            elif isinstance(view, Link):
                identity = f"link.{identity}"
            elif isinstance(view, ModelView):
                identity = f"object.{identity}"
            else:
                raise ValueError(f"Unknown view type: {type(view)}")

            # check if identity is already used
            if identity in view_identity_mapping.values():
                raise ValueError(f"Identity '{identity}' is already used by '{[k for k, v in view_identity_mapping.items() if v == identity][0]}'")

            view_identity_mapping[view] = identity

        return view_identity_mapping

    def setup_view(self, view: BaseView) -> None:
        if not isinstance(view, BaseView) and not isinstance(view, DropDown):
            raise ValueError(f"view must be an instance of {BaseView.__name__}")

        super().setup_view(view)

        # set admin
        view.admin = self

        # check if all view identities are unique
        _ = self.view_identity_mapping

    def company_logo_files_loader(self, request: Request) -> Sequence[Tuple[Any, str]]:
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

        for view, identity in self.view_identity_mapping.items():
            if isinstance(view, CustomView):
                references.append((identity, f"Ansicht {view.label}"))
            elif isinstance(view, Link):
                references.append((identity, f"Link {view.label}"))
            elif isinstance(view, ModelView):
                references.append((identity, f"Objekt {view.label}"))

        return references

    def acl_fields_loader(self, request: Request) -> Sequence[Tuple[Any, str]]:
        fields: list[tuple[str, str]] = []

        for view, identity in self.view_identity_mapping.items():
            if isinstance(view, ModelView):
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
                    fields.append((f"{identity}.{field.name}", f"{field.label}"))

        return fields

    def acl_actions_loader(self, request: Request) -> Sequence[Tuple[Any, str]]:
        actions: list[tuple[str, str]] = []

        for view, identity in self.view_identity_mapping.items():
            if isinstance(view, ModelView):
                # add actions to actions
                for action in view.actions:
                    # skip delete action
                    if action == "delete":
                        continue
                    actions.append((f"{identity}.{action}", f"{action}"))

        return actions

    def acl_base_logic(self, view: BaseView, request: Request) -> Union[bool, list[AccessControlList]]:
        # get session
        session = self.session_document.get_session_from_request(request)
        if session is None:
            raise ValueError("Session not found!")

        # check if user is admin
        if session.user.admin:
            return True

        # get identity of view
        identity = self.view_identity_mapping[view]

        # get acls
        acls = session.get_acls(object_filter=identity)

        return acls

    def is_accessible(self, view: BaseView, request: Request) -> Union[bool, list[AccessControlList]]:
        acls = self.acl_base_logic(view=view, request=request)
        if type(acls) is bool:
            return acls  # admin case
        if len(acls) == 0:
            return False  # no acl is set to this view for user
        return acls

    async def is_action_allowed(self, view: BaseView, request: Request, name: str) -> Union[bool, list[AccessControlList]]:
        # get acls by checking if view is accessible
        acls = self.is_accessible(view=view, request=request)
        if type(acls) is bool:
            return acls

        # handle default actions
        if name == "delete":
            return self.can_delete(view=view, request=request, acls=acls)

        # get view identity
        identity = self.view_identity_mapping[view]

        # check if action is allowed by acls
        allowed = False
        for acl in acls:
            if acl.allow_execute:
                if len(acl.specify_actions) == 0:
                    allowed = True
                    break
                else:
                    if f"{identity}.{name}" in acl.specify_actions:
                        allowed = True
                        break
        if not allowed:
            return False
        return acls

    async def is_row_action_allowed(self, view: BaseView, request: Request, name: str) -> Union[bool, list[AccessControlList]]:
        # get acls by checking if view is accessible
        acls = self.is_accessible(view=view, request=request)
        if type(acls) is bool:
            return acls

        # handle default actions
        if name == "view":
            return self.can_view_details(view=view, request=request, acls=acls)
        elif name == "edit":
            return self.can_edit(view=view, request=request, acls=acls)
        elif name == "delete":
            return self.can_delete(view=view, request=request, acls=acls)

        # get view identity
        identity = self.view_identity_mapping[view]

        # check if action is allowed by acls
        allowed = False
        for acl in acls:
            if acl.allow_execute:
                if len(acl.specify_actions) == 0:
                    allowed = True
                    break
                else:
                    if f"{identity}.{name}" in acl.specify_actions:
                        allowed = True
                        break
        if not allowed:
            return False
        return acls

    def can_view_details(self, view: BaseView, request: Request, acls: Union[None, list[AccessControlList]] = None) -> Union[bool, list[AccessControlList]]:
        # get acls by checking if view is accessible
        if acls is None:
            acls = self.is_accessible(view=view, request=request)
        if type(acls) is bool:  # admin case
            return acls

        # check if action is allowed by acls
        allowed = False
        for acl in acls:
            if acl.allow_detail:
                allowed = True
                break
        if not allowed:
            return False
        return acls

    def can_create(self, view: BaseView, request: Request, acls: Union[None, list[AccessControlList]] = None) -> Union[bool, list[AccessControlList]]:
        # get acls by checking if view is accessible
        if acls is None:
            acls = self.is_accessible(view=view, request=request)
        if type(acls) is bool:
            return acls

        # check if view details is allowed
        can_view_details = self.can_view_details(view=view, request=request, acls=acls)
        if not can_view_details:
            return False

        # check if action is allowed by acls
        allowed = False
        for acl in acls:
            if acl.allow_create:
                allowed = True
                break
        if not allowed:
            return False
        return acls

    def can_edit(self, view: BaseView, request: Request, acls: Union[None, list[AccessControlList]] = None) -> Union[bool, list[AccessControlList]]:
        # get acls by checking if view is accessible
        if acls is None:
            acls = self.is_accessible(view=view, request=request)
        if type(acls) is bool:
            return acls

        # check if view details is allowed
        can_view_details = self.can_view_details(view=view, request=request, acls=acls)
        if not can_view_details:
            return False

        # check if action is allowed by acls
        allowed = False
        for acl in acls:
            if acl.allow_update:
                allowed = True
                break
        if not allowed:
            return False
        return acls

    def can_delete(self, view: BaseView, request: Request, acls: Union[None, list[AccessControlList]] = None) -> Union[bool, list[AccessControlList]]:
        # get acls by checking if view is accessible
        acls = self.is_accessible(view=view, request=request)
        if type(acls) is bool:
            return acls

        # check if action is allowed by acls
        allowed = False
        for acl in acls:
            if acl.allow_delete:
                allowed = True
                break
        if not allowed:
            return False
        return acls
