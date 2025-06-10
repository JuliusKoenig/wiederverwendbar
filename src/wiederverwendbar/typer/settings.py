from typing import Optional

from pydantic import Field

from wiederverwendbar.rich import RichConsoleSettings


class TyperSettings(RichConsoleSettings):
    cli_name: Optional[str] = Field(default=None, title="CLI Name", description="The name of the CLI.")
    cli_help: Optional[str] = Field(default=None, title="CLI Help", description="The help of the CLI.")
