from typing import Optional, Sequence

from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette_admin.i18n import lazy_gettext as _
from starlette_admin.i18n import I18nConfig
from starlette_admin.views import CustomView
from starlette_admin.auth import BaseAuthProvider

from wiederverwendbar.starlette_admin.admin import BaseAdmin
from wiederverwendbar.starlette_admin.settings.settings import AdminSettings


class SettingsAdminMeta(type):
    def __new__(cls, name, bases, attrs):
        # combine settings_cls from bases and attrs
        all_settings_classes = []
        # get settings_class from attrs
        if "settings_class" in attrs:
            # skip duplicates
            if attrs["settings_class"] not in all_settings_classes:
                # add at the beginning of the combined list
                all_settings_classes.append(attrs["settings_class"])

        # get all settings_classes from bases
        for base in bases:
            if hasattr(base, "settings_classes"):
                for settings_class in base.settings_classes:
                    # skip duplicates
                    if settings_class in all_settings_classes:
                        continue
                    # add at the beginning of the combined list
                    all_settings_classes.append(settings_class)

        # set settings_classes to the combined list
        attrs["settings_classes"] = all_settings_classes

        return super().__new__(cls, name, bases, attrs)


class SettingsAdmin(BaseAdmin, metaclass=SettingsAdminMeta):
    settings_class = AdminSettings
    settings_classes: Sequence[type[AdminSettings]] = []

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
            session_middleware: Optional[type[SessionMiddleware]] = None,
            debug: Optional[bool] = None,
            i18n_config: Optional[I18nConfig] = None,
            favicon_url: Optional[str] = None,
            settings: Optional[AdminSettings] = None
    ):
        # get settings from the settings class if not provided
        settings = settings or self.settings_class()
        for settings_class in self.settings_classes:
            if not isinstance(settings, settings_class):
                raise ValueError(f"settings must be an instance of {settings_class.__name__}")

        # set the values from the settings class if not provided
        title = _(title) or _(settings.admin_title)
        base_url = base_url or settings.admin_base_url
        route_name = route_name or settings.admin_route_name
        logo_url = logo_url or settings.admin_logo_url
        login_logo_url = login_logo_url or settings.admin_login_logo_url
        templates_dir = templates_dir or settings.admin_templates_dir
        statics_dir = statics_dir or settings.admin_static_dir
        auth_provider = auth_provider or None
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
