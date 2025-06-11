from enum import Enum
from pathlib import Path
from typing import Optional, Union

from pydantic import Field

from wiederverwendbar.branding import BrandingSettings
from wiederverwendbar.default import Default
from wiederverwendbar.fastapi.auth.schemes import AVAILABLE_AUTH_SCHEMES


class FastAPISettings(BrandingSettings):
    api_debug: bool = Field(default=False, title="FastAPI Debug", description="Whether the FastAPI is in debug mode.")
    api_title: Union[None, Default, str] = Field(default=Default(), title="FastAPI Title", description="The title of the FastAPI.")
    api_summary: Optional[str] = Field(default=None, title="FastAPI Summary", description="The summary of the FastAPI.")
    api_description: Union[None, Default, str] = Field(default=Default(), title="FastAPI Description", description="The description of the FastAPI.")
    api_version: Union[None, Default, str] = Field(default=Default(), title="FastAPI Version", description="The version of the FastAPI.")
    api_openapi_url: Optional[str] = Field(default="/openapi.json", title="FastAPI OpenAPI URL", description="The OpenAPI URL of the FastAPI.")
    api_redirect_slashes: bool = Field(default=True, title="FastAPI Redirect Slashes", description="Whether the FastAPI redirects slashes.")
    api_favicon: Optional[Path] = Field(default=None, title="FastAPI Favicon", description="The favicon of the FastAPI.")
    api_docs_url: Optional[str] = Field(default="/docs", title="FastAPI Docs URL", description="The docs URL of the FastAPI.")
    api_docs_title: Union[None, Default, str] = Field(default=Default(), title="FastAPI Docs Title", description="The title of the FastAPI docs.")
    api_docs_favicon: Union[None, Default, Path] = Field(default=Default(), title="FastAPI Docs Favicon", description="The favicon of the FastAPI docs.")
    api_redoc_url: Optional[str] = Field(default="/redoc", title="FastAPI Redoc URL", description="The Redoc URL of the FastAPI.")
    api_redoc_title: Union[None, Default, str] = Field(default=Default(), title="FastAPI Redoc Title", description="The title of the FastAPI Redoc.")
    api_redoc_favicon: Union[None, Default, Path] = Field(default=Default(), title="FastAPI Redoc Favicon", description="The favicon of the FastAPI Redoc.")
    api_terms_of_service: Union[None, Default, str] = Field(default=Default(), title="FastAPI Terms of Service", description="The terms of service of the FastAPI.")
    api_contact: Union[None, Default, dict[str, str]] = Field(default=Default(), title="FastAPI Contact", description="The contact of the FastAPI.")
    api_license_info: Union[None, Default, dict[str, str]] = Field(default=Default(), title="FastAPI License Info", description="The license info of the FastAPI.")
    api_root_path: str = Field(default="", title="FastAPI Root Path", description="The root path of the FastAPI.")
    api_root_path_in_servers: bool = Field(default=True, title="FastAPI Root Path in Servers", description="Whether the root path of the FastAPI is in servers.")
    api_deprecated: Optional[bool] = Field(default=None, title="FastAPI Deprecated", description="Whether the FastAPI is deprecated.")
    api_info_url: Optional[str] = Field(default="/info", title="FastAPI Info URL", description="The info URL of the FastAPI.")
    api_version_url: Optional[str] = Field(default="/version", title="FastAPI Version URL", description="The version URL of the FastAPI.")

    class RootRedirect(str, Enum):
        DOCS = "docs"
        REDOC = "redoc"

    api_root_redirect: Union[None, Default, RootRedirect, str] = Field(default=Default(), title="FastAPI Root Redirect", description="The root redirect of the FastAPI.")
    api_auth_scheme: AVAILABLE_AUTH_SCHEMES = Field(default=None, title="FastAPI Auth scheme", description="The auth scheme of the FastAPI.")
