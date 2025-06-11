import inspect
import logging
from pathlib import Path
from typing import Optional, Union, Any, Callable, Awaitable, Annotated

from fastapi import FastAPI as _FastAPI, Request, Depends
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html, get_swagger_ui_oauth2_redirect_html
from pydantic import BaseModel, Field, computed_field
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response

from wiederverwendbar.default import Default
from wiederverwendbar.fastapi.auth.schemes import AVAILABLE_AUTH_SCHEMES
from wiederverwendbar.fastapi.settings import FastAPISettings

logger = logging.getLogger(__name__)


class InfoModel(BaseModel):
    title: str = Field(..., title="Title", description="The title of the application.")
    description: str = Field(..., title="Description", description="The description of the application.")
    version: str = Field(..., title="Version", description="The version of the application.")

    class Contact(BaseModel):
        name: str = Field(..., title="Name", description="The name of the contact.")
        email: str = Field(..., title="Email", description="The email of the contact.")

    contact: Optional[Contact] = Field(None, title="Contact", description="The contact of the application.")

    class LicenseInfo(BaseModel):
        name: str = Field(..., title="Name", description="The name of the license.")
        url: str = Field(..., title="URL", description="The URL of the license.")

    license_info: Optional[LicenseInfo] = Field(None, title="License Info", description="The license info of the application.")
    terms_of_service: Optional[str] = Field(None, title="Terms of Service", description="The terms of service of the application.")


class VersionModel(BaseModel):
    version: Union[None, Default, str] = Field(default=Default(), title="Version", description="The version of the application.")

    @computed_field(title="Version Major", description="The major version of the application.")
    @property
    def version_major(self) -> Optional[int]:
        if self.version is None:
            return None
        return int(self.version.split(".")[0])

    @computed_field(title="Version Minor", description="The minor version of the application.")
    @property
    def version_minor(self) -> Optional[int]:
        if self.version is None:
            return None
        return int(self.version.split(".")[1])

    @computed_field(title="Version Patch", description="The patch version of the application.")
    @property
    def version_patch(self) -> Optional[int]:
        if self.version is None:
            return None
        return int(self.version.split(".")[2])


class FastAPI(_FastAPI):
    def __init__(self,
                 debug: Union[None, Default, bool] = Default(),
                 title: Union[None, Default, str] = Default(),
                 summary: Union[None, Default, str] = Default(),
                 description: Union[None, Default, str] = Default(),
                 version: Union[None, Default, str] = Default(),
                 openapi_url: Union[None, Default, str] = Default(),
                 redirect_slashes: Union[None, Default, bool] = Default(),
                 favicon: Union[None, Default, Path] = Default(),
                 docs_url: Union[None, Default, str] = Default(),
                 docs_title: Union[None, Default, str] = Default(),
                 docs_favicon: Union[None, Default, Path] = Default(),
                 redoc_url: Union[None, Default, str] = Default(),
                 redoc_title: Union[None, Default, str] = Default(),
                 redoc_favicon: Union[None, Default, Path] = Default(),
                 terms_of_service: Union[None, Default, str] = Default(),
                 contact: Union[None, Default, dict[str, str]] = Default(),
                 license_info: Union[None, Default, dict[str, str]] = Default(),
                 root_path: Union[None, Default, str] = Default(),
                 root_path_in_servers: Union[None, Default, bool] = Default(),
                 deprecated: Union[None, Default, bool] = Default(),
                 info_url: Union[None, Default, str] = Default(),
                 info_response_model: Union[Default, type[InfoModel]] = Default(),
                 version_url: Union[None, Default, str] = Default(),
                 version_response_model: Union[Default, type[InfoModel]] = Default(),
                 root_redirect: Union[Default, None, FastAPISettings.RootRedirect, str] = Default(),
                 auth_scheme: Union[Default, AVAILABLE_AUTH_SCHEMES] = Default(),
                 settings: Optional[FastAPISettings] = None,
                 **kwargs):

        # set default
        if settings is None:
            settings = FastAPISettings()
        if type(debug) is Default:
            debug = settings.api_debug
        if type(title) is Default:
            title = settings.api_title
        if type(title) is Default:
            title = settings.branding_title
        if title is None:
            title = "FastAPI"
        if type(summary) is Default:
            summary = settings.api_summary
        if type(description) is Default:
            description = settings.api_description
        if type(description) is Default:
            description = settings.branding_description
        if description is None:
            description = ""
        if type(version) is Default:
            version = settings.api_version
        if type(version) is Default:
            version = settings.branding_version
        if version is None:
            version = "0.1.0"
        if type(openapi_url) is Default:
            openapi_url = settings.api_openapi_url
        if type(redirect_slashes) is Default:
            redirect_slashes = settings.api_redirect_slashes
        if type(favicon) is Default:
            favicon = settings.api_favicon
        if type(docs_url) is Default:
            docs_url = settings.api_docs_url
        if type(docs_title) is Default:
            docs_title = settings.api_docs_title
        if type(docs_title) is Default:
            docs_title = title
        if type(docs_favicon) is Default:
            docs_favicon = settings.api_docs_favicon
        if type(docs_favicon) is Default:
            docs_favicon = favicon
        if type(redoc_url) is Default:
            redoc_url = settings.api_redoc_url
        if type(redoc_title) is Default:
            redoc_title = settings.api_redoc_title
        if type(redoc_title) is Default:
            redoc_title = title
        if type(redoc_favicon) is Default:
            redoc_favicon = settings.api_redoc_favicon
        if type(redoc_favicon) is Default:
            redoc_favicon = favicon
        if type(terms_of_service) is Default:
            terms_of_service = settings.api_terms_of_service
        if type(terms_of_service) is Default:
            terms_of_service = settings.branding_terms_of_service
        if type(contact) is Default:
            contact = settings.api_contact
        if type(contact) is Default:
            if settings.branding_author is not None and settings.branding_author_email is not None:
                contact = {"name": settings.branding_author,
                           "email": settings.branding_author_email}
        if type(contact) is Default:
            contact = None
        if type(license_info) is Default:
            license_info = settings.api_license_info
        if type(license_info) is Default:
            if settings.branding_license is not None and settings.branding_license_url is not None:
                license_info = {"name": settings.branding_license,
                                "url": settings.branding_license_url}
        if type(license_info) is Default:
            license_info = None
        if type(root_path) is Default:
            root_path = settings.api_root_path
        if root_path_in_servers is None:
            root_path_in_servers = settings.api_root_path_in_servers
        if type(deprecated) is Default:
            deprecated = settings.api_deprecated
        if type(info_url) is Default:
            info_url = settings.api_info_url
        if type(info_response_model) is Default:
            info_response_model = InfoModel
        if type(version_url) is Default:
            version_url = settings.api_version_url
        if type(version_response_model) is Default:
            version_response_model = VersionModel
        if type(root_redirect) is Default:
            root_redirect = settings.api_root_redirect
        if type(root_redirect) is Default:
            if docs_url is not None:
                root_redirect = FastAPISettings.RootRedirect.DOCS
            elif redoc_url is not None:
                root_redirect = FastAPISettings.RootRedirect.REDOC
            else:
                root_redirect = None
        if type(auth_scheme) is Default:
            auth_scheme = settings.api_auth_scheme

        # set attrs
        self.docs_title = docs_title
        self.docs_favicon = docs_favicon
        self.docs_favicon_url = "/swagger-favicon.ico"
        self.redoc_title = redoc_title
        self.redoc_favicon = redoc_favicon
        self.redoc_favicon_url = "/redoc-favicon.ico"
        self.info_url = info_url
        self.info_response_model = info_response_model
        self.version_url = version_url
        self.version_response_model = version_response_model
        self.root_redirect = root_redirect
        self.auth_scheme = auth_scheme

        # For storing the original "add_api_route" method from router.
        # If None, the access to router will be blocked.
        self._original_add_route: Union[None, bool, Callable, Any] = None
        self._original_add_api_route: Union[None, bool, Callable, Any] = None
        self._original_add_api_websocket_route: Union[None, bool, Callable, Any] = None

        super().__init__(debug=debug,
                         title=title,
                         summary=summary,
                         description=description,
                         version=version,
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
                         **kwargs)

        logger.info(f"Initialized FastAPI: {self}")

    def __str__(self):
        return f"{self.__class__.__name__}(title={self.title}, version={self.version})"

    def __getattribute__(self, item):
        # block router access if the init flag is not set
        if item == "router":
            if self._original_add_route is None or self._original_add_api_route is None or self._original_add_api_websocket_route is None:
                raise RuntimeError("Class is not initialized!")
        return super().__getattribute__(item)

    def _add_route(self,
                   path: str,
                   endpoint: Callable[[Request], Union[Awaitable[Response], Response]],
                   methods: Optional[list[str]] = None,
                   name: Optional[str] = None,
                   include_in_schema: bool = True, *args, **kwargs) -> None:
        if self._original_add_route is None or self._original_add_route is True:
            raise RuntimeError("Original add_route method is not set!")
        logger.debug(f"Adding route for {self} -> {path}")
        return self._original_add_route(path, endpoint, methods, name, include_in_schema, *args, **kwargs)

    def _add_api_route(self,
                       path: str,
                       endpoint: Callable[..., Any],
                       *args,
                       **kwargs) -> None:
        if self._original_add_api_route is None or self._original_add_api_route is True:
            raise RuntimeError("Original add_api_route method is not set!")

        # get protected_flag
        protected_flag = getattr(endpoint, "_protected", False)

        if protected_flag and self.auth_scheme is not None:
            logger.debug(f"Adding protected API route for {self} -> {path}")
            endpoint_signature = inspect.signature(endpoint)
            endpoint_signature_parameters = list(endpoint_signature.parameters.values())
            endpoint_signature_parameters.append(inspect.Parameter(name="credentials",
                                                                   kind=inspect.Parameter.KEYWORD_ONLY,
                                                                   annotation=Annotated[str, Depends(self.auth_scheme())]))
            endpoint.__signature__ = endpoint_signature.replace(parameters=endpoint_signature_parameters)
        else:
            logger.debug(f"Adding API route for {self} -> {path}")
        return self._original_add_api_route(path, endpoint, *args, **kwargs)

    def _add_api_websocket_route(self,
                                 path: str,
                                 endpoint: Callable[..., Any],
                                 name: Optional[str] = None,
                                 *args,
                                 **kwargs) -> None:
        if self._original_add_api_websocket_route is None or self._original_add_api_websocket_route is True:
            raise RuntimeError("Original add_api_websocket_route method is not set!")
        logger.debug(f"Adding API websocket route for {self} -> {path}")
        return self._original_add_api_websocket_route(path, endpoint, name, *args, **kwargs)

    def setup(self) -> None:
        # to unblock router access
        self._original_add_route = True
        self._original_add_api_route = True
        self._original_add_api_websocket_route = True

        # overwrite add_api_route for router
        # noinspection PyTypeChecker
        self._original_add_api_route = self.router.add_api_route
        self.router.add_api_route = self._add_api_route
        # noinspection PyTypeChecker
        self._original_add_api_websocket_route = self.router.add_api_websocket_route
        self.router.add_api_websocket_route = self._add_api_websocket_route
        # noinspection PyTypeChecker
        self._original_add_route = self.router.add_route
        self.router.add_route = self._add_route

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
            self.add_api_route(path=self.info_url, endpoint=self.get_info, response_model=self.info_response_model)

        # create version route
        if self.version_url:
            self.add_api_route(path=self.version_url, endpoint=self.get_version, response_model=self.version_response_model)

        # create root redirect route
        if self.root_redirect:
            self.add_route(path="/", route=self.get_root_redirect, include_in_schema=False)

        # include auth_scheme router
        if self.auth_scheme:
            self.include_router(self.auth_scheme.router)

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

    async def get_version(self, request: Request) -> dict[str, Any]:
        return {"version": self.version}

    async def get_root_redirect(self, request: Request) -> RedirectResponse:
        root_path = request.scope.get("root_path", "").rstrip("/")
        if self.root_redirect is None:
            raise RuntimeError("Root Redirect not set")
        root_redirect = self.root_redirect
        if root_redirect == FastAPISettings.RootRedirect.DOCS:
            if self.docs_url is None:
                raise RuntimeError("Docs URL not set")
            root_redirect = root_path + self.docs_url
        if root_redirect == FastAPISettings.RootRedirect.REDOC:
            if self.redoc_url is None:
                raise RuntimeError("Redoc URL not set")
            root_redirect = root_path + self.redoc_url
        return RedirectResponse(url=root_redirect)
