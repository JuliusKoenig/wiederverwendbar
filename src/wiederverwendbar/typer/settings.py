from typing import Union

from pydantic import Field

from wiederverwendbar.branding.settings import BrandingSettings
from wiederverwendbar.default import Default
from wiederverwendbar.rich.settings import RichConsoleSettings


class TyperSettings(RichConsoleSettings, BrandingSettings):
    cli_name: Union[None, Default, str] = Field(default=Default(), title="CLI Name", description="The name of the CLI.")
    cli_help: Union[None, Default, str] = Field(default=Default(), title="CLI Help", description="The help of the CLI.")
    cli_info_enabled: bool = Field(default=True, title="Info Command", description="Enable the info command.")
    cli_version_enabled: bool = Field(default=True, title="Version Command", description="Enable the version command.")
