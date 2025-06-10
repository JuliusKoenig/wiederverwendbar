from typing import Union, Any

from pydantic import Field

from wiederverwendbar.default import Default
from wiederverwendbar.rich import RichConsoleSettings


class TyperSettings(RichConsoleSettings):
    cli_name: Union[None, Default, str] = Field(default=Default(), title="CLI Name", description="The name of the CLI.")
    cli_help: Union[None, Default, str] = Field(default=Default(), title="CLI Help", description="The help of the CLI.")

    def model_post_init(self, context: Any, /):
        super().model_post_init(context)

        if type(self.cli_name) is Default:
            self.cli_name = None

        if type(self.cli_help) is Default:
            self.cli_help = None
