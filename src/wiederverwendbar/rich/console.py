from typing import Optional, Literal, Union, Any

from rich._log_render import FormatTimeCallable
from rich.console import Console as _RichConsole
from rich.style import StyleType
from rich.theme import Theme

from wiederverwendbar.console.console import Console as _Console
from wiederverwendbar.console.out_files import OutFiles
from wiederverwendbar.rich.settings import RichConsoleSettings


class RichConsole(_Console, _RichConsole):
    def __init__(self,
                 *,
                 console_file: Optional[OutFiles] = None,
                 console_seperator: Optional[str] = None,
                 console_end: Optional[str] = None,
                 console_color_system: Optional[Literal["auto", "standard", "256", "truecolor", "windows"]] = None,
                 console_force_terminal: Optional[bool] = None,
                 console_force_jupyter: Optional[bool] = None,
                 console_force_interactive: Optional[bool] = None,
                 console_soft_wrap: Optional[bool] = None,
                 console_theme: Optional[Theme] = None,  # ToDo: not in settings included
                 console_quiet: Optional[bool] = None,
                 console_width: Optional[int] = None,
                 console_height: Optional[int] = None,
                 console_style: Optional[StyleType] = None,  # ToDo: not in settings included
                 console_no_color: Optional[bool] = None,
                 console_tab_size: Optional[int] = None,
                 console_record: Optional[bool] = None,
                 console_markup: Optional[bool] = None,
                 console_emoji: Optional[bool] = None,
                 console_emoji_variant: Optional[Literal["emoji", "text"]] = None,
                 console_highlight: Optional[bool] = None,
                 console_log_time: Optional[bool] = None,
                 console_log_path: Optional[bool] = None,
                 console_log_time_format: Union[str, FormatTimeCallable] = "[%X]",  # ToDo: not in settings included
                 settings: Optional[RichConsoleSettings] = None,
                 **kwargs):
        """
        Create a new rich console.

        :param console_file: Console file. Default is STDOUT.
        :param console_seperator: Console seperator. Default is a space.
        :param console_end: Console end. Default is a newline.
        :param settings: A settings object to use. If None, defaults to ConsoleSettings().
        """

        if settings is None:
            settings = RichConsoleSettings()
        _Console.__init__(self, console_file=console_file, console_seperator=console_seperator, console_end=console_end, settings=settings)

        if console_color_system is None:
            console_color_system = settings.console_color_system
        self.console_color_system = console_color_system
        if console_force_terminal is None:
            console_force_terminal = settings.console_force_terminal
        self.console_force_terminal = console_force_terminal
        if console_force_jupyter is None:
            console_force_jupyter = settings.console_force_jupyter
        self.console_force_jupyter = console_force_jupyter
        if console_force_interactive is None:
            console_force_interactive = settings.console_force_interactive
        self.console_force_interactive = console_force_interactive
        if console_soft_wrap is None:
            console_soft_wrap = settings.console_soft_wrap
        self.console_soft_wrap = console_soft_wrap
        # if console_theme is None: # ToDo: not in settings included
        #     console_theme = settings.console_theme
        # self.console_theme = console_theme # ToDo: not in settings included
        if console_quiet is None:
            console_quiet = settings.console_quiet
        self.console_quiet = console_quiet
        if console_width is None:
            console_width = settings.console_width
        self.console_width = console_width
        if console_height is None:
            console_height = settings.console_height
        self.console_height = console_height
        # if console_style is None: # ToDo: not in settings included
        #     console_style = settings.console_style # ToDo: not in settings included
        # self.console_style = console_style # ToDo: not in settings included
        if console_no_color is None:
            console_no_color = settings.console_no_color
        self.console_no_color = console_no_color
        if console_tab_size is None:
            console_tab_size = settings.console_tab_size
        self.console_tab_size = console_tab_size
        if console_record is None:
            console_record = settings.console_record
        self.console_record = console_record
        if console_markup is None:
            console_markup = settings.console_markup
        self.console_markup = console_markup
        if console_emoji is None:
            console_emoji = settings.console_emoji
        self.console_emoji = console_emoji
        if console_emoji_variant is None:
            console_emoji_variant = settings.console_emoji_variant
        self.console_emoji_variant = console_emoji_variant
        if console_highlight is None:
            console_highlight = settings.console_highlight
        self.console_highlight = console_highlight
        if console_log_time is None:
            console_log_time = settings.console_log_time
        self.console_log_time = console_log_time
        if console_log_path is None:
            console_log_path = settings.console_log_path
        self.console_log_path = console_log_path
        # if console_log_time_format is None: # ToDo: not in settings included
        #     console_log_time_format = settings.console_log_time_format # ToDo: not in settings included
        # self.console_log_time_format = console_log_time_format # ToDo: not in settings included

        _RichConsole.__init__(self,
                              color_system=console_color_system,
                              force_terminal=console_force_terminal,
                              force_jupyter=console_force_jupyter,
                              force_interactive=console_force_interactive,
                              soft_wrap=console_soft_wrap,
                              theme=console_theme,
                              quiet=console_quiet,
                              width=console_width,
                              height=console_height,
                              style=console_style,
                              no_color=console_no_color,
                              tab_size=console_tab_size,
                              record=console_record,
                              markup=console_markup,
                              emoji=console_emoji,
                              emoji_variant=console_emoji_variant,
                              highlight=console_highlight,
                              log_time=console_log_time,
                              log_path=console_log_path,
                              log_time_format=console_log_time_format)

    def print(self,
              *args: Any,
              sep: Optional[str] = None,
              end: Optional[str] = None,
              **kwargs) -> None:
        """
        Prints the values.

        :param args: values to be printed.
        :param sep:  string inserted between values, default a space.
        :param end:  string appended after the last value, default a newline.
        :param kwargs: Additional parameters.
        """

        if sep is None:
            sep = self.console_seperator
        if end is None:
            end = self.console_end
        _RichConsole.print(self, *args, sep=sep, end=end, **kwargs)
