from typing import Optional, Literal

from pydantic import Field

from wiederverwendbar.console.settings import ConsoleSettings


class RichConsoleSettings(ConsoleSettings):
    color_system: Optional[Literal["auto", "standard", "256", "truecolor", "windows"]] = Field(default="auto", title="Console Color System",
                                                                                               description="The color system of the console.")
    force_terminal: Optional[bool] = Field(default=None, title="Console Force Terminal", description="Whether to force the terminal.")
    force_jupyter: Optional[bool] = Field(default=None, title="Console Force Jupyter", description="Whether to force Jupyter.")
    force_interactive: Optional[bool] = Field(default=None, title="Console Force Interactive", description="Whether to force interactive mode.")
    soft_wrap: bool = Field(default=False, title="Console Soft Wrap", description="Whether to soft wrap the console.")
    quiet: bool = Field(default=False, title="Console Quiet", description="Whether to suppress all output.")
    width: Optional[int] = Field(default=None, title="Console Width", description="The width of the console.")
    height: Optional[int] = Field(default=None, title="Console Height", description="The height of the console.")
    no_color: Optional[bool] = Field(default=None, title="Console No Color", description="Whether to disable color.")
    tab_size: int = Field(default=8, title="Console Tab Size", description="The tab size of the console.")
    record: bool = Field(default=False, title="Console Record", description="Whether to record the console output.")
    markup: bool = Field(default=True, title="Console Markup", description="Whether to enable markup.")
    emoji: bool = Field(default=True, title="Console Emoji", description="Whether to enable emoji.")
    emoji_variant: Optional[Literal["emoji", "text"]] = Field(default=None, title="Console Emoji Variant", description="The emoji variant of the console.")
    highlight: bool = Field(default=True, title="Console Highlight", description="Whether to enable highlighting.")
    log_time: bool = Field(default=True, title="Console Log Time", description="Whether to log the time.")
    log_path: bool = Field(default=True, title="Console Log Path", description="Whether to log the path (logging of the caller by).")
