from typing import Optional, Sequence

from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette_admin.i18n import I18nConfig
from starlette_admin.views import CustomView
from starlette_admin.auth import BaseAuthProvider

from wiederverwendbar.starlette_admin.settings.admin import SettingsAdmin
from wiederverwendbar.starlette_admin.form_max_fields.settings import FormMaxFieldsAdminSettings


class FormMaxFieldsAdmin(SettingsAdmin):
    settings_class = FormMaxFieldsAdminSettings

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
            form_max_fields: Optional[int] = None,
            settings: Optional[FormMaxFieldsAdminSettings] = None
    ):
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
            session_middleware=session_middleware,
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
