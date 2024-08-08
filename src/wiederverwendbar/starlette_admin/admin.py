from typing import Union, Optional, Sequence

from jinja2 import BaseLoader, ChoiceLoader, FileSystemLoader, PackageLoader
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount
from starlette.middleware import Middleware
from starlette.staticfiles import StaticFiles
from starlette.types import ASGIApp
from starlette_admin.base import BaseAdmin
from starlette_admin.i18n import lazy_gettext as _
from starlette_admin.i18n import I18nConfig
from starlette_admin.views import CustomView
from starlette_admin.auth import BaseAuthProvider

from wiederverwendbar.starlette_admin.settings import AdminSettings, FormMaxFieldsAdminSettings


class MultiPathAdminMeta(type):
    def __new__(cls, name, bases, attrs):
        # combine static_files_packages from bases and attrs
        all_static_files_packages = []
        # get all static_files_packages from bases
        for base in bases:
            if hasattr(base, "static_files_packages"):
                for static_files_package in base.static_files_packages:
                    # skip duplicates
                    if static_files_package in all_static_files_packages:
                        continue
                    # add at the beginning of the combined list
                    all_static_files_packages.append(static_files_package)
        # get static_files_packages from attrs
        if "static_files_packages" in attrs:
            for static_files_package in attrs["static_files_packages"]:
                # skip duplicates
                if static_files_package in all_static_files_packages:
                    continue
                # add at the beginning of the combined list
                all_static_files_packages.append(static_files_package)

        # set static_files_packages to the combined list
        attrs["static_files_packages"] = all_static_files_packages

        # combine template_packages from bases and attrs
        all_template_packages = []
        # get all template_packages from bases
        for base in bases:
            if hasattr(base, "template_packages"):
                for template_package in base.template_packages:
                    # skip duplicates
                    if template_package in all_template_packages:
                        continue
                    # add at the beginning of the combined list
                    all_template_packages.append(template_package)

        # get template_packages from attrs
        if "template_packages" in attrs:
            for template_package in attrs["template_packages"]:
                # skip duplicates
                if template_package in all_template_packages:
                    continue
                # add at the beginning of the combined list
                all_template_packages.append(template_package)

        # set template_packages to the combined list
        attrs["template_packages"] = all_template_packages

        return super().__new__(cls, name, bases, attrs)


class MultiPathAdmin(BaseAdmin, metaclass=MultiPathAdminMeta):
    """
    A base class for Admin classes that can be used in multiple paths.
    In detail, it combines the static_files_packages and template_packages from all bases and attrs.
    """

    static_files_packages: list[Union[str, tuple[str, str]]] = ["starlette_admin"]
    template_packages: list[BaseLoader] = [PackageLoader("starlette_admin", "templates")]

    def init_routes(self) -> None:
        super().init_routes()

        # find the statics mount index
        statics_index = None
        for i, route in enumerate(self.routes):
            if isinstance(route, Mount) and route.name == "statics":
                statics_index = i
                break
        if statics_index is None:
            raise ValueError("Could not find statics mount")

        # reverse static files packages
        self.static_files_packages.reverse()

        # override the static files route
        self.routes[statics_index] = Mount("/statics", app=StaticFiles(directory=self.statics_dir, packages=self.static_files_packages), name="statics")

    def _setup_templates(self) -> None:
        super()._setup_templates()

        # reverse template packages
        self.template_packages.reverse()

        self.templates.env.loader = ChoiceLoader(
            [
                FileSystemLoader(self.templates_dir),
                *self.template_packages,
            ]
        )


class SettingsAdmin(BaseAdmin):
    class SettingsMiddleware(BaseHTTPMiddleware):
        def __init__(self, app: ASGIApp, admin: "SettingsAdmin") -> None:
            super().__init__(app)
            self.admin = admin

        async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
            # add settings to request state
            request.state.settings = self.admin.settings

            return await call_next(request)

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
            auth_provider: Optional[BaseAuthProvider] = None,
            middlewares: Optional[Sequence[Middleware]] = None,
            debug: Optional[bool] = None,
            i18n_config: Optional[I18nConfig] = None,
            favicon_url: Optional[str] = None,
            settings: Optional[AdminSettings] = None
    ):
        # get settings from the settings class if not provided
        settings = settings or AdminSettings()
        if not isinstance(settings, AdminSettings):
            raise ValueError(f"settings must be an instance of {AdminSettings.__name__}")

        # set the values from the settings class if not provided
        title = _(title) or _(settings.admin_title)
        base_url = base_url or settings.admin_base_url
        route_name = route_name or settings.admin_route_name
        logo_url = logo_url or settings.admin_logo_url
        login_logo_url = login_logo_url or settings.admin_login_logo_url
        templates_dir = templates_dir or settings.admin_templates_dir
        statics_dir = statics_dir or settings.admin_static_dir
        auth_provider = auth_provider or None
        middlewares = middlewares or []
        debug = debug if debug is not None else settings.admin_debug
        i18n_config = i18n_config or I18nConfig(default_locale=settings.admin_language.value,
                                                language_cookie_name=settings.admin_language_cookie_name,
                                                language_header_name=settings.admin_language_header_name,
                                                language_switcher=settings.admin_language_available)
        favicon_url = favicon_url or settings.admin_favicon_url

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
        )

        # set the settings
        self.settings = settings

        # add the settings middleware
        settings_middleware = Middleware(
            self.SettingsMiddleware,  # noqa
            admin=self
        )
        self.middlewares.insert(0, settings_middleware)


class FormMaxFieldsAdmin(SettingsAdmin):
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
            auth_provider: Optional[BaseAuthProvider] = None,
            middlewares: Optional[Sequence[Middleware]] = None,
            debug: Optional[bool] = None,
            i18n_config: Optional[I18nConfig] = None,
            favicon_url: Optional[str] = None,
            form_max_fields: Optional[int] = None,
            settings: Optional[FormMaxFieldsAdminSettings] = None
    ):
        # get settings from the settings class if not provided
        settings = settings or FormMaxFieldsAdminSettings()
        if not isinstance(settings, FormMaxFieldsAdminSettings):
            raise ValueError(f"settings must be an instance of {FormMaxFieldsAdminSettings.__name__}")

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

        self.form_max_fields = form_max_fields or settings.form_max_fields

    async def _render_create(self, request: Request) -> Response:
        self._form_func = request.form
        request.form = self.form

        return await super()._render_create(request)

    async def _render_edit(self, request: Request) -> Response:
        self._form_func = request.form
        request.form = self.form

        return await super()._render_edit(request)

    async def form(self, *args, **kwargs):
        if "max_fields" not in kwargs:
            kwargs["max_fields"] = self.form_max_fields

        return await self._form_func(*args, **kwargs)
