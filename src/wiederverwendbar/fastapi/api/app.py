import logging
from pathlib import Path
from typing import Optional, Union, Any

from fastapi import Request
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html, get_swagger_ui_oauth2_redirect_html
from starlette.responses import FileResponse, HTMLResponse, JSONResponse

from wiederverwendbar.branding import BrandingSettings
from wiederverwendbar.default import Default
from wiederverwendbar.fastapi.api.settings import ApiAppSettings
from wiederverwendbar.fastapi.api.models import InfoModel
from wiederverwendbar.fastapi.root.app import RootApp
from wiederverwendbar.pydantic.types.version import Version

logger = logging.getLogger(__name__)


class ApiApp(RootApp):
    def __init__(self,
                 debug: Union[Default, bool] = Default(),
                 title: Union[Default, str] = Default(),
                 summary: Union[None, Default, str] = Default(),
                 description: Union[Default, str] = Default(),
                 version: Union[Default, Version] = Default(),
                 openapi_url: Union[None, Default, str] = Default(),
                 redirect_slashes: Union[Default, bool] = Default(),
                 favicon: Union[None, Default, Path] = Default(),
                 docs_url: Union[None, Default, str] = Default(),
                 docs_title: Union[Default, str] = Default(),
                 docs_favicon: Union[None, Default, Path] = Default(),
                 redoc_url: Union[None, Default, str] = Default(),
                 redoc_title: Union[Default, str] = Default(),
                 redoc_favicon: Union[None, Default, Path] = Default(),
                 terms_of_service: Union[None, Default, str] = Default(),
                 contact: Union[None, Default, dict[str, str]] = Default(),
                 license_info: Union[None, Default, dict[str, str]] = Default(),
                 root_path: Union[Default, str] = Default(),
                 root_path_in_servers: Union[Default, bool] = Default(),
                 deprecated: Union[None, Default, bool] = Default(),
                 info_url: Union[None, Default, str] = Default(),
                 info_tags: Union[Default, list[str]] = Default(),
                 info_response_model: Union[Default, type[InfoModel]] = Default(),
                 version_url: Union[None, Default, str] = Default(),
                 version_tags: Union[Default, list[str]] = Default(),
                 root_redirect: Union[Default, None, ApiAppSettings.RootRedirect, str] = Default(),
                 settings: Optional[ApiAppSettings] = None,
                 branding_settings: Optional[BrandingSettings] = None,
                 **kwargs):

        # set default
        if settings is None:
            settings = ApiAppSettings()
        if branding_settings is None:
            branding_settings = BrandingSettings()

        if type(debug) is Default:
            debug = settings.debug
        if type(debug) is Default:
            debug = False

        if type(title) is Default:
            title = settings.title
        if type(title) is Default:
            title = branding_settings.title
        if type(title) is Default:
            title = "FastAPI"

        if type(summary) is Default:
            summary = settings.summary
        if type(summary) is Default:
            summary = None

        if type(description) is Default:
            description = settings.description
        if type(description) is Default:
            description = branding_settings.description
        if type(description) is Default:
            description = ""

        if type(version) is Default:
            version = settings.version
        if type(version) is Default:
            version = branding_settings.version
        if type(version) is Default:
            version = Version("0.1.0")

        if type(openapi_url) is Default:
            openapi_url = settings.openapi_url
        if type(openapi_url) is Default:
            openapi_url = "/openapi.json"

        if type(redirect_slashes) is Default:
            redirect_slashes = settings.redirect_slashes
        if type(redirect_slashes) is Default:
            redirect_slashes = True

        if type(favicon) is Default:
            favicon = settings.favicon
        if type(favicon) is Default:
            favicon = None

        if type(docs_url) is Default:
            docs_url = settings.docs_url
        if type(docs_url) is Default:
            docs_url = "/docs"

        if type(docs_title) is Default:
            docs_title = settings.docs_title
        if type(docs_title) is Default:
            docs_title = title

        if type(docs_favicon) is Default:
            docs_favicon = settings.docs_favicon
        if type(docs_favicon) is Default:
            docs_favicon = favicon

        if type(redoc_url) is Default:
            redoc_url = settings.redoc_url
        if type(redoc_url) is Default:
            redoc_url = "/redoc"

        if type(redoc_title) is Default:
            redoc_title = settings.redoc_title
        if type(redoc_title) is Default:
            redoc_title = title

        if type(redoc_favicon) is Default:
            redoc_favicon = settings.redoc_favicon
        if type(redoc_favicon) is Default:
            redoc_favicon = favicon

        if type(terms_of_service) is Default:
            terms_of_service = settings.terms_of_service
        if type(terms_of_service) is Default:
            terms_of_service = branding_settings.terms_of_service
        if type(terms_of_service) is Default:
            terms_of_service = None

        if type(contact) is Default:
            contact = settings.contact
        if type(contact) is Default:
            if type(branding_settings.author) is str and type(branding_settings.author_email) is str:
                contact = {"name": branding_settings.author,
                           "email": branding_settings.author_email}
        if type(contact) is Default:
            contact = None

        if type(license_info) is Default:
            license_info = settings.license_info
        if type(license_info) is Default:
            if type(branding_settings.license) is str and type(branding_settings.license_url) is str:
                license_info = {"name": branding_settings.license,
                                "url": branding_settings.license_url}
        if type(license_info) is Default:
            license_info = None

        if type(root_path) is Default:
            root_path = settings.root_path
        if type(root_path) is Default:
            root_path = ""
        # ToDo

        if root_path_in_servers is None:
            root_path_in_servers = settings.root_path_in_servers
        if type(root_path_in_servers) is Default:
            root_path_in_servers = True
        # ToDo

        if type(deprecated) is Default:
            deprecated = settings.deprecated
        if type(deprecated) is Default:
            deprecated = None

        if type(info_url) is Default:
            info_url = settings.info_url
        if type(info_url) is Default:
            info_url = "/info"

        if type(info_tags) is Default:
            info_tags = settings.info_tags
        if type(info_tags) is Default:
            info_tags = []
        if len(info_tags) == 0:
            info_tags = ["default"]

        if type(info_response_model) is Default:
            info_response_model = InfoModel

        if type(version_url) is Default:
            version_url = settings.version_url
        if type(version_url) is Default:
            version_url = "/version"

        if type(version_tags) is Default:
            version_tags = settings.version_tags
        if type(version_tags) is Default:
            version_tags = []
        if len(version_tags) == 0:
            info_tags = ["default"]

        if type(root_redirect) is Default:
            root_redirect = settings.root_redirect
        if type(root_redirect) is Default:
            if docs_url is not None:
                root_redirect = ApiAppSettings.RootRedirect.DOCS
            elif redoc_url is not None:
                root_redirect = ApiAppSettings.RootRedirect.REDOC
        if type(root_redirect) is Default:
            root_redirect = None

        # set attrs
        self.docs_title = docs_title
        self.docs_favicon = docs_favicon
        self.docs_favicon_url = "/swagger-favicon.ico"
        self.redoc_title = redoc_title
        self.redoc_favicon = redoc_favicon
        self.redoc_favicon_url = "/redoc-favicon.ico"
        self.info_url = info_url
        self.info_tags = info_tags
        self.info_response_model = info_response_model
        self.version_url = version_url
        self.version_tags = version_tags

        super().__init__(debug=debug,
                         title=title,
                         summary=summary,
                         description=description,
                         version=str(version),
                         openapi_url=openapi_url,
                         redirect_slashes=redirect_slashes,
                         docs_url=docs_url,
                         redoc_url=redoc_url,
                         terms_of_service=terms_of_service,
                         contact=contact,
                         license_info=license_info,
                         root_path=root_path,
                         root_path_in_servers=root_path_in_servers,
                         deprecated=deprecated,
                         root_redirect=root_redirect,
                         settings=settings,
                         **kwargs)

    def setup(self) -> None:
        super().setup()

        # create openapi route
        if self.openapi_url:
            self.add_route(path=self.openapi_url, route=self.get_openapi, include_in_schema=False)

        # create docs routes
        if self.openapi_url and self.docs_url:
            if self.docs_favicon is not None:
                self.add_route(path=self.docs_favicon_url, route=self.get_docs_favicon, include_in_schema=False)
            self.add_route(path=self.docs_url, route=self.get_docs, include_in_schema=False)
            if self.swagger_ui_oauth2_redirect_url:
                self.add_route(path=self.swagger_ui_oauth2_redirect_url, route=self.get_docs_redirect, include_in_schema=False)

        # create redoc routes
        if self.openapi_url and self.redoc_url:
            if self.redoc_favicon is not None:
                self.add_route(path=self.docs_favicon_url, route=self.get_redoc_favicon, include_in_schema=False)
            self.add_route(path=self.redoc_url, route=self.get_redoc, include_in_schema=False)

        # create info route
        if self.info_url:
            self.add_api_route(path=self.info_url, endpoint=self.get_info, response_model=self.info_response_model, tags=self.info_tags)

        # create version route
        if self.version_url:
            self.add_api_route(path=self.version_url, endpoint=self.get_version, response_model=Version, tags=self.version_tags)

    async def get_openapi(self, request: Request) -> JSONResponse:
        root_path = request.scope.get("root_path", "").rstrip("/")
        server_urls = {url for url in (server_data.get("url") for server_data in self.servers) if url}
        if root_path not in server_urls:
            if root_path and self.root_path_in_servers:
                self.servers.insert(0, {"url": root_path})
                server_urls.add(root_path)
        return JSONResponse(self.openapi())

    async def get_docs_favicon(self, request: Request) -> FileResponse:
        return FileResponse(self.docs_favicon)

    async def docs_parameters(self, request: Request) -> dict[str, Any]:
        docs_kwargs = {"title": self.docs_title}
        root_path = request.scope.get("root_path", "").rstrip("/")
        if self.openapi_url is None:
            raise RuntimeError("OpenAPI URL not set")
        docs_kwargs["openapi_url"] = root_path + self.openapi_url
        if self.swagger_ui_oauth2_redirect_url:
            docs_kwargs["oauth2_redirect_url"] = root_path + self.swagger_ui_oauth2_redirect_url
        docs_kwargs["init_oauth"] = self.swagger_ui_init_oauth
        docs_kwargs["swagger_ui_parameters"] = self.swagger_ui_parameters
        if self.docs_favicon is not None:
            docs_kwargs["swagger_favicon_url"] = self.docs_favicon_url
        return docs_kwargs

    async def get_docs(self, request: Request) -> HTMLResponse:
        return get_swagger_ui_html(**await self.docs_parameters(request))

    async def get_docs_redirect(self, request: Request) -> HTMLResponse:
        return get_swagger_ui_oauth2_redirect_html()

    async def redoc_parameters(self, request: Request) -> dict[str, Any]:
        redoc_kwargs = {"title": self.redoc_title}
        root_path = request.scope.get("root_path", "").rstrip("/")
        if self.openapi_url is None:
            raise RuntimeError("OpenAPI URL not set")
        redoc_kwargs["openapi_url"] = root_path + self.openapi_url
        if self.redoc_favicon is not None:
            redoc_kwargs["redoc_favicon_url"] = self.redoc_favicon_url
        return redoc_kwargs

    async def get_redoc_favicon(self, request: Request) -> FileResponse:
        return FileResponse(self.redoc_favicon)

    async def get_redoc(self, request: Request) -> HTMLResponse:
        return get_redoc_html(**await self.redoc_parameters(request=request))

    async def get_info(self, request: Request) -> dict[str, Any]:
        return {"title": self.title,
                "description": self.description,
                "version": self.version,
                "contact": self.contact,
                "license_info": self.license_info,
                "terms_of_service": self.terms_of_service}

    async def get_version(self, request: Request) -> str:
        return self.version

    async def get_root_redirect(self, request: Request) -> tuple[str, int]:
        if self.root_redirect == ApiAppSettings.RootRedirect.DOCS:
            if self.docs_url is None:
                raise RuntimeError("Docs URL not set")
            return request.scope.get("root_path", "").rstrip("/") + self.docs_url, 307
        elif self.root_redirect == ApiAppSettings.RootRedirect.REDOC:
            if self.redoc_url is None:
                raise RuntimeError("Redoc URL not set")
            return request.scope.get("root_path", "").rstrip("/") + self.redoc_url, 307
        return await super().get_root_redirect(request=request)
