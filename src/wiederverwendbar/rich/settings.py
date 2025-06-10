from typing import Optional, Literal

from pydantic import Field

from wiederverwendbar.console.settings import ConsoleSettings


class RichConsoleSettings(ConsoleSettings):
    console_color_system: Optional[Literal["auto", "standard", "256", "truecolor", "windows"]] = Field(default="auto", title="Console Color System",
                                                                                                       description="The color system of the console.")
    console_force_terminal: Optional[bool] = Field(default=None, title="Console Force Terminal", description="Whether to force the terminal.")
    console_force_jupyter: Optional[bool] = Field(default=None, title="Console Force Jupyter", description="Whether to force Jupyter.")
    console_force_interactive: Optional[bool] = Field(default=None, title="Console Force Interactive", description="Whether to force interactive mode.")
    console_soft_wrap: bool = Field(default=False, title="Console Soft Wrap", description="Whether to soft wrap the console.")
    console_quiet: bool = Field(default=False, title="Console Quiet", description="Whether to suppress all output.")
    console_width: Optional[int] = Field(default=None, title="Console Width", description="The width of the console.")
    console_height: Optional[int] = Field(default=None, title="Console Height", description="The height of the console.")
    console_no_color: Optional[bool] = Field(default=None, title="Console No Color", description="Whether to disable color.")
    console_tab_size: int = Field(default=8, title="Console Tab Size", description="The tab size of the console.")
    console_record: bool = Field(default=False, title="Console Record", description="Whether to record the console output.")
    console_markup: bool = Field(default=True, title="Console Markup", description="Whether to enable markup.")
    console_emoji: bool = Field(default=True, title="Console Emoji", description="Whether to enable emoji.")
    console_emoji_variant: Optional[Literal["emoji", "text"]] = Field(default=None, title="Console Emoji Variant", description="The emoji variant of the console.")
    console_highlight: bool = Field(default=True, title="Console Highlight", description="Whether to enable highlighting.")
    console_log_time: bool = Field(default=True, title="Console Log Time", description="Whether to log the time.")
    console_log_path: bool = Field(default=True, title="Console Log Path", description="Whether to log the path (logging of the caller by).")
