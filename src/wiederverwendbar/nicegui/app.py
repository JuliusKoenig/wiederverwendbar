import logging
from pathlib import Path
from typing import Optional, Union, Any, Callable

from fastapi import Request
from nicegui import ui, core
from nicegui.language import Language
from starlette.middleware.gzip import GZipMiddleware
from starlette.types import ASGIApp
from starlette.routing import Route, Mount

from wiederverwendbar.branding import BrandingSettings
from wiederverwendbar.default import Default
from wiederverwendbar.fastapi.root.app import RootApp
from wiederverwendbar.nicegui.settings import NiceGUISettings
from wiederverwendbar.pydantic.types.version import Version

logger = logging.getLogger(__name__)


class NiceGUIApp(RootApp):
    def __init__(self,
                 root: Union[None, Default, Callable] = Default(),
                 debug: Union[Default, bool] = Default(),
                 title: Union[Default, str] = Default(),
                 version: Union[Default, Version] = Default(),
                 viewport: Union[Default, str] = Default(),
                 favicon: Union[None, Default, str, Path] = Default(),
                 dark: Union[None, Default, bool] = Default(),
                 language: Union[Default, Language] = Default(),
                 binding_refresh_interval: Union[None, Default, float] = Default(),
                 reconnect_timeout: Union[Default, float] = Default(),
                 message_history_length: Union[Default, int] = Default(),
                 cache_control_directives: Union[Default, str] = Default(),
                 gzip_middleware_factory: Union[None, Default, Callable[[ASGIApp], GZipMiddleware]] = Default(),
                 tailwind: Union[Default, bool] = Default(),
                 prod_js: Union[Default, bool] = Default(),
                 storage_secret: Union[None, Default, str] = Default(),
                 session_middleware_kwargs: Union[None, Default, dict[str, Any]] = Default(),
                 nicegui_mount_path: Union[Default, str] = Default(),
                 root_path: Union[Default, str] = Default(),
                 root_path_in_servers: Union[Default, bool] = Default(),
                 root_redirect: Union[Default, None, str] = Default(),
                 settings: Optional[NiceGUISettings] = None,
                 branding_settings: Optional[BrandingSettings] = None,
                 **kwargs):

        # set default
        if settings is None:
            settings = NiceGUISettings()
        if branding_settings is None:
            branding_settings = BrandingSettings()

        if type(root) is Default:
            root = None

        if type(debug) is Default:
            debug = settings.debug
        if type(debug) is Default:
            debug = False

        if type(title) is Default:
            title = settings.title
        if type(title) is Default:
            title = branding_settings.title
        if type(title) is Default:
            title = "NiceGUI"

        if type(version) is Default:
            version = settings.version
        if type(version) is Default:
            version = branding_settings.version
        if type(version) is Default:
            version = Version("0.1.0")

        if type(viewport) is Default:
            viewport = settings.viewport
        if type(viewport) is Default:
            viewport = "width=device-width, initial-scale=1"

        if type(favicon) is Default:
            favicon = settings.favicon
        if type(favicon) is Default:
            favicon = None

        if type(dark) is Default:
            dark = settings.dark
        if type(dark) is Default:
            dark = False

        if type(language) is Default:
            language = settings.language
        if type(language) is Default:
            language = "de-DE"

        if type(binding_refresh_interval) is Default:
            binding_refresh_interval = settings.binding_refresh_interval
        if type(binding_refresh_interval) is Default:
            binding_refresh_interval = 0.1

        if type(reconnect_timeout) is Default:
            reconnect_timeout = settings.reconnect_timeout
        if type(reconnect_timeout) is Default:
            reconnect_timeout = 3.0

        if type(message_history_length) is Default:
            message_history_length = settings.message_history_length
        if type(message_history_length) is Default:
            message_history_length = 1000

        if type(cache_control_directives) is Default:
            cache_control_directives = settings.cache_control_directives
        if type(cache_control_directives) is Default:
            cache_control_directives = "public, max-age=31536000, immutable, stale-while-revalidate=31536000"

        if type(gzip_middleware_factory) is Default:
            gzip_middleware_factory = GZipMiddleware

        if type(tailwind) is Default:
            tailwind = settings.tailwind
        if type(tailwind) is Default:
            tailwind = True

        if type(prod_js) is Default:
            prod_js = settings.prod_js
        if type(prod_js) is Default:
            prod_js = debug

        if type(storage_secret) is Default:
            storage_secret = settings.storage_secret
        if type(storage_secret) is Default:
            storage_secret = None

        if type(session_middleware_kwargs) is Default:
            session_middleware_kwargs = None

        if type(nicegui_mount_path) is Default:
            nicegui_mount_path = "/"

        # set attrs
        self.root = root
        self.viewport = viewport
        self.favicon = favicon
        self.dark = dark
        # noinspection PyTypeChecker
        self.language: Language = language
        self.binding_refresh_interval = binding_refresh_interval
        self.reconnect_timeout = reconnect_timeout
        self.message_history_length = message_history_length
        self.cache_control_directives = cache_control_directives
        self.gzip_middleware_factory = gzip_middleware_factory
        self.tailwind = tailwind
        self.prod_js = prod_js
        self.storage_secret = storage_secret
        self.session_middleware_kwargs = session_middleware_kwargs
        self.nicegui_mount_path = nicegui_mount_path

        super().__init__(debug=debug,
                         title=title,
                         version=str(version),
                         root_path=root_path,
                         root_path_in_servers=root_path_in_servers,
                         root_redirect=root_redirect,
                         settings=settings,
                         **kwargs)

    def setup(self) -> None:
        super().setup()

        ui.run_with(app=self,
                    root=self.root,
                    title=self.title,
                    viewport=self.viewport,
                    favicon=self.favicon,
                    dark=self.dark,
                    language=self.language,
                    binding_refresh_interval=self.binding_refresh_interval,
                    reconnect_timeout=self.reconnect_timeout,
                    message_history_length=self.message_history_length,
                    cache_control_directives=self.cache_control_directives,
                    gzip_middleware_factory=self.gzip_middleware_factory,
                    mount_path=self.nicegui_mount_path,
                    on_air=None,
                    tailwind=self.tailwind,
                    prod_js=self.prod_js,
                    storage_secret=self.storage_secret,
                    session_middleware_kwargs=self.session_middleware_kwargs,
                    show_welcome_message=False)

    async def get_root_redirect(self, request: Request) -> tuple[str, int]:
        for route in core.app.routes:
            if not isinstance(route, Route) and not isinstance(route, Mount):
                continue
            if route.path.startswith("/_nicegui"):
                continue
            redirect_path = request.scope.get("root_path", "").rstrip("/")
            redirect_path += "" if self.nicegui_mount_path == "/" else self.nicegui_mount_path
            redirect_path += "" if route.path == "/" else route.path
            return redirect_path, 307
        return await super().get_root_redirect(request=request)
