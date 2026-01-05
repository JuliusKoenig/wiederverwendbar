from enum import Enum
from pathlib import Path
from typing import Union

from wiederverwendbar.default import Default
from wiederverwendbar.printable_settings import PrintableSettings, Field
from wiederverwendbar.pydantic.types.version import Version


class FastAPISettings(PrintableSettings):
    debug: Union[Default, bool] = Field(default=Default(), title="FastAPI Debug", description="Whether the FastAPI is in debug mode.")
    title: Union[Default, str] = Field(default=Default(), title="FastAPI Title", description="The title of the FastAPI.")
    summary: Union[None, Default, str] = Field(default=Default(), title="FastAPI Summary", description="The summary of the FastAPI.")
    description: Union[Default, str] = Field(default=Default(), title="FastAPI Description", description="The description of the FastAPI.")
    version: Union[Default, Version] = Field(default=Default(), title="FastAPI Version", description="The version of the FastAPI.")
    openapi_url: Union[None, Default, str] = Field(default=Default(), title="FastAPI OpenAPI URL", description="The OpenAPI URL of the FastAPI.")
    redirect_slashes: Union[Default, bool] = Field(default=Default(), title="FastAPI Redirect Slashes", description="Whether the FastAPI redirects slashes.")
    favicon: Union[None, Default, Path] = Field(default=Default(), title="FastAPI Favicon", description="The favicon of the FastAPI.")
    docs_url: Union[None, Default, str] = Field(default=Default(), title="FastAPI Docs URL", description="The docs URL of the FastAPI.")
    docs_title: Union[Default, str] = Field(default=Default(), title="FastAPI Docs Title", description="The title of the FastAPI docs.")
    docs_favicon: Union[None, Default, Path] = Field(default=Default(), title="FastAPI Docs Favicon", description="The favicon of the FastAPI docs.")
    redoc_url: Union[None, Default, str] = Field(default=Default(), title="FastAPI Redoc URL", description="The Redoc URL of the FastAPI.")
    redoc_title: Union[Default, str] = Field(default=Default(), title="FastAPI Redoc Title", description="The title of the FastAPI Redoc.")
    redoc_favicon: Union[None, Default, Path] = Field(default=Default(), title="FastAPI Redoc Favicon", description="The favicon of the FastAPI Redoc.")
    terms_of_service: Union[None, Default, str] = Field(default=Default(), title="FastAPI Terms of Service", description="The terms of service of the FastAPI.")
    contact: Union[None, Default, dict[str, str]] = Field(default=Default(), title="FastAPI Contact", description="The contact of the FastAPI.")
    license_info: Union[None, Default, dict[str, str]] = Field(default=Default(), title="FastAPI License Info", description="The license info of the FastAPI.")
    root_path: Union[Default, str] = Field(default=Default(), title="FastAPI Root Path", description="The root path of the FastAPI.")
    root_path_in_servers: Union[Default, bool] = Field(default=Default(), title="FastAPI Root Path in Servers", description="Whether the root path of the FastAPI is in servers.")
    deprecated: Union[None, Default, str] = Field(default=Default(), title="FastAPI Deprecated", description="Whether the FastAPI is deprecated.")
    info_url: Union[None, Default, str] = Field(default=Default(), title="FastAPI Info URL", description="The info URL of the FastAPI.")
    info_tags: Union[Default, list[str]] = Field(default=Default(), title="FastAPI Info tags", description="The info tags for info route in OpenAPI schema.")
    version_url: Union[None, Default, str] = Field(default=Default(), title="FastAPI Version URL", description="The version URL of the FastAPI.")
    version_tags: Union[Default, list[str]] = Field(default=Default(), title="FastAPI Version tags", description="The version tags for version route in OpenAPI schema.")

    class RootRedirect(str, Enum):
        DOCS = "docs"
        REDOC = "redoc"

    api_root_redirect: Union[None, Default, RootRedirect, str] = Field(default=Default(), title="FastAPI Root Redirect", description="The root redirect of the FastAPI.")
