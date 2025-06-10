from typing import Any

from pydantic import Field

from wiederverwendbar.branding.settings import BrandingSettings
from wiederverwendbar.default import Default
from wiederverwendbar.typer.settings import TyperSettings


class TyperBrandingSettings(TyperSettings, BrandingSettings):
    cli_info_enabled: bool = Field(default=True, title="Info Command", description="Enable the info command.")
    cli_version_enabled: bool = Field(default=True, title="Version Command", description="Enable the version command.")

    def model_post_init(self, context: Any, /):
        if type(self.cli_name) is Default:
            self.cli_name = self.branding_title

        if type(self.cli_help) is Default:
            self.cli_help = self.branding_description

        super().model_post_init(context)
