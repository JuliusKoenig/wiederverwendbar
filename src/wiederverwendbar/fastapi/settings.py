from enum import Enum
from pathlib import Path
from typing import Union

from pydantic import Field

from wiederverwendbar.branding import BrandingSettings
from wiederverwendbar.default import Default
from wiederverwendbar.pydantic.types.version import Version


class FastAPISettings(BrandingSettings):
    api_debug: Union[Default, bool] = Field(default=Default(), title="FastAPI Debug", description="Whether the FastAPI is in debug mode.")
    api_title: Union[Default, str] = Field(default=Default(), title="FastAPI Title", description="The title of the FastAPI.")
    api_summary: Union[None, Default, str] = Field(default=Default(), title="FastAPI Summary", description="The summary of the FastAPI.")
    api_description: Union[Default, str] = Field(default=Default(), title="FastAPI Description", description="The description of the FastAPI.")
    api_version: Union[Default, Version] = Field(default=Default(), title="FastAPI Version", description="The version of the FastAPI.")
    api_openapi_url: Union[None, Default, str] = Field(default=Default(), title="FastAPI OpenAPI URL", description="The OpenAPI URL of the FastAPI.")
    api_redirect_slashes: Union[Default, bool] = Field(default=Default(), title="FastAPI Redirect Slashes", description="Whether the FastAPI redirects slashes.")
    api_favicon: Union[None, Default, Path] = Field(default=Default(), title="FastAPI Favicon", description="The favicon of the FastAPI.")
    api_docs_url: Union[None, Default, str] = Field(default=Default(), title="FastAPI Docs URL", description="The docs URL of the FastAPI.")
    api_docs_title: Union[Default, str] = Field(default=Default(), title="FastAPI Docs Title", description="The title of the FastAPI docs.")
    api_docs_favicon: Union[None, Default, Path] = Field(default=Default(), title="FastAPI Docs Favicon", description="The favicon of the FastAPI docs.")
    api_redoc_url: Union[None, Default, str] = Field(default=Default(), title="FastAPI Redoc URL", description="The Redoc URL of the FastAPI.")
    api_redoc_title: Union[Default, str] = Field(default=Default(), title="FastAPI Redoc Title", description="The title of the FastAPI Redoc.")
    api_redoc_favicon: Union[None, Default, Path] = Field(default=Default(), title="FastAPI Redoc Favicon", description="The favicon of the FastAPI Redoc.")
    api_terms_of_service: Union[None, Default, str] = Field(default=Default(), title="FastAPI Terms of Service", description="The terms of service of the FastAPI.")
    api_contact: Union[None, Default, dict[str, str]] = Field(default=Default(), title="FastAPI Contact", description="The contact of the FastAPI.")
    api_license_info: Union[None, Default, dict[str, str]] = Field(default=Default(), title="FastAPI License Info", description="The license info of the FastAPI.")
    api_root_path: Union[Default, str] = Field(default=Default(), title="FastAPI Root Path", description="The root path of the FastAPI.")
    api_root_path_in_servers: Union[Default, bool] = Field(default=Default(), title="FastAPI Root Path in Servers", description="Whether the root path of the FastAPI is in servers.")
    api_deprecated: Union[None, Default, str] = Field(default=Default(), title="FastAPI Deprecated", description="Whether the FastAPI is deprecated.")
    api_info_url: Union[None, Default, str] = Field(default=Default(), title="FastAPI Info URL", description="The info URL of the FastAPI.")
    api_info_tags: list[str] = Field(default_factory=lambda: ["Info"], title="FastAPI Info tags", description="The info tags for info route in OpenAPI schema.")
    api_version_url: Union[None, Default, str] = Field(default=Default(), title="FastAPI Version URL", description="The version URL of the FastAPI.")
    api_version_tags: list[str] = Field(default_factory=lambda: ["Info"], title="FastAPI Version tags", description="The version tags for version route in OpenAPI schema.")

    class RootRedirect(str, Enum):
        DOCS = "docs"
        REDOC = "redoc"

    api_root_redirect: Union[None, Default, RootRedirect, str] = Field(default=Default(), title="FastAPI Root Redirect", description="The root redirect of the FastAPI.")
