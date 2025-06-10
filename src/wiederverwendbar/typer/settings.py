from typing import Union

from pydantic import Field

from wiederverwendbar.default import Default
from wiederverwendbar.rich import RichConsoleSettings


class TyperSettings(RichConsoleSettings):
    cli_name: Union[None, Default, str] = Field(default=Default(), title="CLI Name", description="The name of the CLI.")
    cli_help: Union[None, Default, str] = Field(default=Default(), title="CLI Help", description="The help of the CLI.")
