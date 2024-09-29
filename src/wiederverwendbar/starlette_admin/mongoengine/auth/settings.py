from pathlib import Path
from typing import Optional

from pydantic import Field

from wiederverwendbar.starlette_admin.settings.settings import AdminSettings


class MongoengineAdminAuthSettings(AdminSettings):
    admin_auth: bool = Field(default=True, title="Admin Auth", description="Whether the admin panel requires authentication.")
    admin_login_path: str = Field(default="/login", title="Admin Login Path", description="The path of the login page of the admin panel.")
    admin_logout_path: str = Field(default="/logout", title="Admin Logout Path", description="The path of the logout page of the admin panel.")
    admin_allow_routes: Optional[list[str]] = Field(default=None, title="Admin Allow Routes", description="The routes that are allowed without authentication in the admin panel.")
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

    @property
    def admin_static_company_logo_dir(self) -> Path:
        if self.admin_static_dir is None:
            raise FileNotFoundError("Admin static directory is not set. Please set it to the directory of the admin panel static.")

        company_logo_dir = Path(self.admin_static_dir) / self.admin_company_logo_dir
        if not company_logo_dir.is_dir():
            raise FileNotFoundError(f"Admin company logo directory {company_logo_dir} is not a directory.")
        return company_logo_dir
