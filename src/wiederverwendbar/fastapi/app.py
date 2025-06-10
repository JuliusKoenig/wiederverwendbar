from pathlib import Path
from typing import Optional, Union

from fastapi import FastAPI as _FastAPI
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from starlette.responses import FileResponse

from wiederverwendbar.default import Default
from wiederverwendbar.fastapi.settings import FastAPISettings


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
                 separate_input_output_schemas: Union[None, Default, bool] = Default(),
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
        if type(separate_input_output_schemas) is Default:
            separate_input_output_schemas = settings.api_separate_input_output_schemas

        super().__init__(debug=debug,
                         title=title,
                         summary=summary,
                         description=description,
                         version=version,
                         openapi_url=openapi_url,
                         redirect_slashes=redirect_slashes,
                         docs_url=None,
                         redoc_url=None,
                         terms_of_service=terms_of_service,
                         contact=contact,
                         license_info=license_info,
                         root_path=root_path,
                         root_path_in_servers=root_path_in_servers,
                         deprecated=deprecated,
                         separate_input_output_schemas=separate_input_output_schemas,
                         **kwargs)

        # create docs
        if docs_url is not None:
            docs_kwargs = {"title": docs_title,
                           "openapi_url": openapi_url}
            if docs_favicon is not None:
                docs_kwargs["swagger_favicon_url"] = "/swagger-favicon.ico"
                @self.get("/swagger-favicon.ico", include_in_schema=False)
                async def favicon() -> FileResponse:
                    return FileResponse(docs_favicon)

            @self.get(docs_url, include_in_schema=False)
            async def swagger():
                return get_swagger_ui_html(**docs_kwargs)

        if docs_url is not None:
            redoc_kwargs = {"title": redoc_title,
                           "openapi_url": openapi_url}
            if redoc_favicon is not None:
                redoc_kwargs["redoc_favicon_url"] = "/redoc-favicon.ico"
                @self.get("/redoc-favicon.ico", include_in_schema=False)
                async def favicon() -> FileResponse:
                    return FileResponse(redoc_favicon)

            @self.get(redoc_url, include_in_schema=False)
            async def redoc():
                return get_redoc_html(**redoc_kwargs)
