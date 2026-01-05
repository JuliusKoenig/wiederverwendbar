from typing import Union

from pydantic import Field

from wiederverwendbar.default import Default
from wiederverwendbar.printable_settings import PrintableSettings
from wiederverwendbar.pydantic.types.version import Version


class TyperSettings(PrintableSettings):
    title: Union[Default, str] = Field(default=Default(), title="CLI Title", description="The title of the CLI.")
    description: Union[Default, str] = Field(default=Default(), title="CLI Description", description="The description of the CLI.")
    version: Union[Default, Version] = Field(default=Default(), title="CLI Version", description="The version of the CLI.")
    terms_of_service: Union[None, Default, str] = Field(default=Default(), title="CLI Terms of Service", description="The terms of service of the CLI.")
    contact: Union[None, Default, dict[str, str]] = Field(default=Default(), title="CLI Contact", description="The contact of the CLI.")
    license_info: Union[None, Default, dict[str, str]] = Field(default=Default(), title="CLI License Info", description="The license info of the CLI.")
    name: Union[None, Default, str] = Field(default=Default(), title="CLI Name", description="The name of the CLI.")
    help: Union[None, Default, str] = Field(default=Default(), title="CLI Help", description="The help of the CLI.")
    info_enabled: Union[Default, bool] = Field(default=Default(), title="Info Command", description="Enable the info command.")
    version_enabled: Union[Default, bool] = Field(default=Default(), title="Version Command", description="Enable the version command.")
