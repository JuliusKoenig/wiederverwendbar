import warnings
from enum import Enum
from pathlib import Path
from typing import Optional, Any

from pydantic import BaseModel, Field, DirectoryPath
from starlette.datastructures import State
from starlette.requests import Request

from starlette_admin.i18n import SUPPORTED_LOCALES


class AdminSettings(BaseModel):
    admin_title: str = Field(default="Admin", title="Admin Title", description="The title of the admin panel.")
    admin_name: str = Field(default="admin", pattern=r"^[a-zA-Z0-9_-]+$", title="Admin Name", description="The name of the admin panel.")
    admin_base_url: str = Field(default="/admin", title="Admin Base URL", description="The base URL of the admin panel.")
    admin_route_name: str = Field(default="admin", title="Admin Route Name", description="The route name of the admin panel.")
    admin_logo_url: Optional[str] = Field(default="logo.png", title="Admin Logo URL", description="The URL of the admin panel logo.")
    admin_login_logo_url: Optional[str] = Field(default="logo.png", title="Admin Login Logo URL", description="The URL of the admin panel login logo.")
    admin_templates_dir: DirectoryPath = Field(default=..., title="Admin Templates Directory", description="The directory of the admin panel templates.")
    admin_static_dir: Optional[DirectoryPath] = Field(default=None, title="Admin static Directory", description="The directory of the admin panel static.")
    admin_debug: bool = Field(default=False, title="Admin Debug", description="Whether the admin panel is in debug mode.")

    class Language(str, Enum):
        DE = "de" if "de" in SUPPORTED_LOCALES else ValueError("German is not a supported locale")
        EN = "en" if "en" in SUPPORTED_LOCALES else ValueError("English is not a supported locale")
        FR = "fr" if "fr" in SUPPORTED_LOCALES else ValueError("French is not a supported locale")
        RU = "ru" if "ru" in SUPPORTED_LOCALES else ValueError("Russian is not a supported locale")
        TR = "tr" if "tr" in SUPPORTED_LOCALES else ValueError("Turkish is not a supported locale")

    admin_language: Language = Field(default=Language.DE, title="Admin Language", description="The language of the admin panel.")
    admin_language_cookie_name: str = Field(default="language", title="Admin Language Cookie Name", description="The name of the admin panel language cookie.")
    admin_language_header_name: str = Field(default="Accept-Language", title="Admin Language Header Name", description="The name of the admin panel language header.")
    admin_language_available: Optional[list[Language]] = Field(default=None, title="Admin Language Available",
                                                               description="The available languages of the admin panel.")
    admin_favicon_url: Optional[str] = Field(default="favicon.ico", title="Admin Favicon URL", description="The URL of the admin panel favicon.")
    admin_session_secret_key: str = Field("change_me", title="Admin Session Secret Key", description="The secret key of the admin panel session.")
    admin_session_cookie: str = Field(default="session", title="Admin Session Cookie", description="The name of the admin panel session cookie.")
    admin_session_max_age: int = Field(default=14 * 24 * 60 * 60, title="Admin Session Max Age",
                                       description="The maximum age of the admin panel session. "
                                                   "If the session is not used for this time, it will be deleted.")
    admin_session_absolute_max_age: Optional[int] = Field(default=14 * 24 * 60 * 60, title="Admin Session Absolute Max Age",
                                                          description="The absolute maximum age of the admin panel session. "
                                                                      "The session will be deleted after this time. If not set, the session will not expire. "
                                                                      "If timeout_max_age is set and this is smaller than timeout_max_age, this will be set to timeout_max_age.")
    admin_session_only_one: bool = Field(default=False, title="Admin Session Only One", description="Whether only one session is allowed for the admin panel.")
    admin_session_path: str = Field(default="/", title="Admin Session Path", description="The path of the admin panel session.")

    class SameSite(str, Enum):
        LAX = "lax"
        STRICT = "strict"
        NONE = "none"

    admin_session_same_site: SameSite = Field(default=SameSite.LAX, title="Admin Session Same Site", description="The same site of the admin panel session.")
    admin_session_https_only: bool = Field(default=False, title="Admin Session HTTPS Only", description="Whether the admin panel session is HTTPS only.")
    admin_session_domain: Optional[str] = Field(None, title="Admin Session Domain", description="The domain of the admin panel session.")

    def __init__(self, /, **data: Any):
        data["admin_templates_dir"] = data.get("admin_templates_dir", Path("templates"))
        super().__init__(**data)

        # check if admin_static_dir is set
        if self.admin_static_dir is None:
            warnings.warn("Admin static directory is not set. Please set it to the directory of the admin panel static.", UserWarning)
        else:
            if not self.admin_static_dir.is_dir():
                raise FileNotFoundError(f"Admin static directory {self.admin_static_dir} is not a directory.")

            admin_logo_file = self.admin_static_dir / self.admin_logo_url
            if admin_logo_file.is_file():
                self.admin_logo_url = f"{self.admin_base_url}/statics/{self.admin_logo_url}"
            else:
                self.admin_logo_url = None
            admin_login_logo_file = self.admin_static_dir / self.admin_login_logo_url
            if admin_login_logo_file.is_file():
                self.admin_login_logo_url = f"{self.admin_base_url}/statics/{self.admin_login_logo_url}"
            else:
                self.admin_login_logo_url = None
            admin_favicon_file = self.admin_static_dir / self.admin_favicon_url
            if admin_favicon_file.is_file():
                self.admin_favicon_url = f"{self.admin_base_url}/statics/{self.admin_favicon_url}"
            else:
                self.admin_favicon_url = None

        # check if and admin_session_secret_key is not the default value
        if self.admin_session_secret_key == self.model_fields.get("admin_session_secret_key").default:
            warnings.warn("Admin session secret key is not set. Please set it to a secure value.", UserWarning)

        # check if admin_session_max_age is greater than admin_session_timeout_max_age
        if self.admin_session_absolute_max_age is not None and self.admin_session_absolute_max_age < self.admin_session_max_age:
            warnings.warn("Admin session absolute max age is smaller than admin session max age. "
                          "Setting admin session absolute max age to admin session max age.", UserWarning)
            self.admin_session_absolute_max_age = self.admin_session_max_age

    @classmethod
    def from_state(cls, state: State):
        settings = state.admin.settings
        if not isinstance(settings, cls):
            raise ValueError(f"Settings is not instance of {cls}")
        return settings