import warnings
from enum import Enum
from pathlib import Path
from typing import Optional, Any

from pydantic import BaseModel, Field, DirectoryPath
from starlette.requests import Request

from starlette_admin.i18n import SUPPORTED_LOCALES


class AdminSettings(BaseModel):
    admin_title: str = Field(default="Admin", title="Admin Title", description="The title of the admin panel.")
    admin_name: str = Field(default="admin", pattern=r"^[a-zA-Z0-9_-]+$", title="Admin Name", description="The name of the admin panel.")
    admin_base_url: str = Field(default="/admin", title="Admin Base URL", description="The base URL of the admin panel.")
    admin_route_name: str = Field(default="admin", title="Admin Route Name", description="The route name of the admin panel.")
    admin_logo_url: Optional[str] = Field(default=None, title="Admin Logo URL", description="The URL of the admin panel logo.")
    admin_login_logo_url: Optional[str] = Field(default=None, title="Admin Login Logo URL", description="The URL of the admin panel login logo.")
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
    admin_favicon_url: Optional[str] = Field(default=None, title="Admin Favicon URL", description="The URL of the admin panel favicon.")

    def __init__(self, /, **data: Any):
        data["admin_templates_dir"] = data.get("admin_templates_dir", Path("templates"))
        super().__init__(**data)

        # check if admin_static_dir is set
        if self.admin_static_dir is None:
            warnings.warn("Admin static directory is not set. Please set it to the directory of the admin panel static.", UserWarning)

    @classmethod
    def from_request(cls, request: Request):
        settings = request.state.settings
        if not isinstance(settings, cls):
            raise ValueError(f"settings must be an instance of {cls.__name__}")
        return settings

    def to_request(self, request: Request) -> Request:
        request.state.settings = self
        return request


class FormMaxFieldsAdminSettings(AdminSettings):
    form_max_fields: int = Field(default=1000, title="Form Max Fields", description="The maximum number of fields in a form.")


class AuthAdminSettings(AdminSettings):
    admin_auth: bool = Field(default=True, title="Admin Auth", description="Whether the admin panel requires authentication.")
    admin_login_path: str = Field(default="/login", title="Admin Login Path", description="The path of the login page of the admin panel.")
    admin_logout_path: str = Field(default="/logout", title="Admin Logout Path", description="The path of the logout page of the admin panel.")
    admin_allow_routes: Optional[list[str]] = Field(default=None, title="Admin Allow Routes", description="The routes that are allowed without authentication in the admin panel.")
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
    admin_user_app_title: str = Field(default="Hallo, {{session.user.username}}!", title="Admin User App Title", description="The title of the admin panel for the user. "
                                                                                                                             "If will be evaluated with the session.")
    admin_company_logo_dir: str = Field(default="company_logo", title="Admin Company Logo Subdirectory",
                                        description="The subdirectory of the admin panel static for the company logos.")
    admin_company_logos_suffixes: list[str] = Field(default=[".png", ".jpg", ".jpeg", ".gif"], title="Admin Company Logos Suffixes",
                                                    description="The suffixes of the company logos in the admin panel static.")
    admin_superuser_username: Optional[str] = Field(default="admin", title="Admin User Superuser username", description="The username of the superuser of the admin panel.")
    admin_superuser_auto_create: bool = Field(default=False, title="Admin User Superuser Auto Create",
                                              description="Whether the superuser is automatically created if it does not exist. The password will be the same as the username.")
    admin_user_allows_empty_password_login: bool = Field(default=False, title="Admin User Allows Empty Password Login",
                                                         description="Whether the user is allowed to login with an empty password.")

    def __init__(self, /, **data: Any):
        super().__init__(**data)

        # check if and admin_session_secret_key is not the default value
        if self.admin_session_secret_key == self.model_fields.get("admin_session_secret_key").default:
            warnings.warn("Admin session secret key is not set. Please set it to a secure value.", UserWarning)

        # check if admin_session_max_age is greater than admin_session_timeout_max_age
        if self.admin_session_absolute_max_age is not None and self.admin_session_absolute_max_age < self.admin_session_max_age:
            warnings.warn("Admin session absolute max age is smaller than admin session max age. "
                          "Setting admin session absolute max age to admin session max age.", UserWarning)
            self.admin_session_absolute_max_age = self.admin_session_max_age

    @property
    def admin_static_company_logo_dir(self) -> Path:
        if self.admin_static_dir is None:
            raise FileNotFoundError("Admin static directory is not set. Please set it to the directory of the admin panel static.")

        company_logo_dir = Path(self.admin_static_dir) / self.admin_company_logo_dir
        if not company_logo_dir.is_dir():
            raise FileNotFoundError(f"Admin company logo directory {company_logo_dir} is not a directory.")
        return company_logo_dir
