from typing import Optional, Any

from pydantic import Field

from wiederverwendbar.rich import RichConsoleSettings


class TyperSettings(RichConsoleSettings):
    cli_name: Optional[str] = Field(default=None, title="CLI Name", description="The name of the CLI.")
    cli_help: Optional[str] = Field(default=None, title="CLI Help", description="The help of the CLI.")

    def model_post_init(self, context: Any, /):
        super().model_post_init(context)

        if self.cli_name is None:
            self.cli_name = self.branding_title

        if self.cli_help is None:
            self.cli_help = self.branding_description
