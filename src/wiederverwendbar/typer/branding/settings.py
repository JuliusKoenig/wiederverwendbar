from pydantic import Field

from wiederverwendbar.branding.settings import BrandingSettings
from wiederverwendbar.typer.settings import TyperSettings


class TyperBrandingSettings(TyperSettings, BrandingSettings):
    cli_info_enabled: bool = Field(default=True, title="Info Command", description="Enable the info command.")
    cli_version_enabled: bool = Field(default=True, title="Version Command", description="Enable the version command.")
