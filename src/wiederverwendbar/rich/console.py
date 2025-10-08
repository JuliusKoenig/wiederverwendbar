from typing import Optional, Literal, Union, Any, IO

from rich.console import Console as _RichConsole

from wiederverwendbar.console.console import Console as _Console
from wiederverwendbar.console.out_files import OutFiles
from wiederverwendbar.rich.settings import RichConsoleSettings


def _print_function(self: "RichConsole", *a, **kw):
    for k in kw.copy():
        if k not in ["color", "header_color", "border_color"]:
            continue
        del kw[k]
    b_file = ...
    if "file" in kw:
        b_file = getattr(self, f"_{self.__class__.__name__}__file")
        self._file = kw["file"]
        del kw["file"]
    _RichConsole.print(self, *a, **kw)
    if b_file is not ...:
        self._file = b_file


class RichConsole(_Console, _RichConsole):
    print_function = _print_function  # _RichConsole.print
    console_exclamation_message_templates = {
        "trace": {**_Console.console_exclamation_message_templates["trace"], **{"prefix_content_color": "purple"}},
        "debug": {**_Console.console_exclamation_message_templates["debug"], **{"prefix_content_color": "cyan"}},
        "info": {**_Console.console_exclamation_message_templates["info"], **{"prefix_content_color": "light_grey"}},
        "warning": {**_Console.console_exclamation_message_templates["warning"], **{"prefix_content_color": "yellow"}},
        "error": {**_Console.console_exclamation_message_templates["error"], **{"prefix_content_color": "red3"}},
        "critical": {**_Console.console_exclamation_message_templates["critical"],
                     **{"prefix_content_color": "dark_red"}},
        "panic": {**_Console.console_exclamation_message_templates["panic"], **{"prefix_content_color": "bright_red"}},
        "okay": {**_Console.console_exclamation_message_templates["okay"], **{"prefix_content_color": "bright_green"}},
        "success": {**_Console.console_exclamation_message_templates["success"],
                    **{"prefix_content_color": "bright_green"}},
        "fail": {**_Console.console_exclamation_message_templates["fail"], **{"prefix_content_color": "red3"}}
    }

    def __init__(self,
                 *,
                 console_file: Optional[OutFiles] = None,
                 console_seperator: Optional[str] = None,
                 console_end: Optional[str] = None,
                 console_exclamation_prefix_brackets_style: Optional[str] = None,
                 console_color_system: Optional[Literal["auto", "standard", "256", "truecolor", "windows"]] = None,
                 console_force_terminal: Optional[bool] = None,
                 console_force_jupyter: Optional[bool] = None,
                 console_force_interactive: Optional[bool] = None,
                 console_soft_wrap: Optional[bool] = None,
                 console_quiet: Optional[bool] = None,
                 console_width: Optional[int] = None,
                 console_height: Optional[int] = None,
                 console_no_color: Optional[bool] = None,
                 console_tab_size: Optional[int] = None,
                 console_record: Optional[bool] = None,
                 console_markup: Optional[bool] = None,
                 console_emoji: Optional[bool] = None,
                 console_emoji_variant: Optional[Literal["emoji", "text"]] = None,
                 console_highlight: Optional[bool] = None,
                 console_log_time: Optional[bool] = None,
                 console_log_path: Optional[bool] = None,
                 settings: Optional[RichConsoleSettings] = None,
                 **kwargs):
        """
        Create a new rich console.

        :param console_file: Console file. Default is STDOUT.
        :param console_seperator: Console seperator. Default is a space.
        :param console_end: Console end. Default is a newline.
        :param console_exclamation_prefix_brackets_style: Console exclamation bracket style. Default is "square".
        :param console_color_system: Rich Console color system.
        :param console_force_terminal: Rich Console force terminal.
        :param console_force_jupyter: Rich Console force jupyter.
        :param console_force_interactive: Rich Console force interactive.
        :param console_soft_wrap: Rich Console soft wrap.
        :param console_quiet: Rich Console quiet.
        :param console_width: Rich Console width.
        :param console_height: Rich Console height.
        :param console_no_color: Rich Console no color.
        :param console_tab_size: Rich Console tab size.
        :param console_record: Rich Console record.
        :param console_markup: Rich Console markup.
        :param console_emoji: Rich Console emoji.
        :param console_emoji_variant: Rich Console emoji variant.
        :param console_highlight: Rich Console highlight.
        :param console_log_time: Rich Console log time.
        :param console_log_path: Rich Console log path.
        :param settings: A settings object to use. If None, defaults to ConsoleSettings().
        """

        if settings is None:
            settings = RichConsoleSettings()

        _Console.__init__(self,
                          console_file=console_file,
                          console_seperator=console_seperator,
                          console_end=console_end,
                          console_exclamation_prefix_brackets_style=console_exclamation_prefix_brackets_style,
                          settings=settings)

        if console_color_system is None:
            console_color_system = settings.console_color_system

        if console_force_terminal is None:
            console_force_terminal = settings.console_force_terminal

        if console_force_jupyter is None:
            console_force_jupyter = settings.console_force_jupyter

        if console_force_interactive is None:
            console_force_interactive = settings.console_force_interactive

        if console_soft_wrap is None:
            console_soft_wrap = settings.console_soft_wrap

        if console_quiet is None:
            console_quiet = settings.console_quiet

        if console_width is None:
            console_width = settings.console_width

        if console_height is None:
            console_height = settings.console_height

        if console_no_color is None:
            console_no_color = settings.console_no_color

        if console_tab_size is None:
            console_tab_size = settings.console_tab_size

        if console_record is None:
            console_record = settings.console_record

        if console_markup is None:
            console_markup = settings.console_markup

        if console_emoji is None:
            console_emoji = settings.console_emoji

        if console_emoji_variant is None:
            console_emoji_variant = settings.console_emoji_variant

        if console_highlight is None:
            console_highlight = settings.console_highlight

        if console_log_time is None:
            console_log_time = settings.console_log_time

        if console_log_path is None:
            console_log_path = settings.console_log_path

        _RichConsole.__init__(self,
                              color_system=console_color_system,
                              force_terminal=console_force_terminal,
                              force_jupyter=console_force_jupyter,
                              force_interactive=console_force_interactive,
                              soft_wrap=console_soft_wrap,
                              quiet=console_quiet,
                              width=console_width,
                              height=console_height,
                              no_color=console_no_color,
                              tab_size=console_tab_size,
                              record=console_record,
                              markup=console_markup,
                              emoji=console_emoji,
                              emoji_variant=console_emoji_variant,
                              highlight=console_highlight,
                              log_time=console_log_time,
                              log_path=console_log_path,
                              **kwargs)

    @property
    def _file(self) -> Optional[IO[str]]:
        if self.__file is not None:
            return self.__file
        return self._console_file.get_file()

    @_file.setter
    def _file(self, value: Optional[IO[str]]) -> None:
        self.__file = value

    def _card_get_text(self,
                       text: str,
                       color: Optional[str] = None,
                       **kwargs) -> str:
        text = super()._card_get_text(text=text,
                                      **kwargs)
        if color is not None:
            text = f"[{color}]{text}[/{color}]"
        return text

    def _card_get_header_text(self,
                              text: str,
                              header_color: Optional[str] = None,
                              **kwargs) -> str:
        text = super()._card_get_header_text(text=text,
                                             **kwargs)
        if header_color is not None:
            text = f"[{header_color}]{text}[/{header_color}]"
        return text

    def _card_get_border(self,
                         border_style: Literal["single_line", "double_line"],
                         border_part: Literal[
                             "horizontal", "vertical", "top_left", "top_right", "bottom_left", "bottom_right", "vertical_left", "vertical_right"],
                         border_color: Optional[str] = None,
                         **kwargs):
        border = super()._card_get_border(border_style=border_style,
                                          border_part=border_part,
                                          **kwargs)
        if border_color is not None:
            border = f"[{border_color}]{border}[/{border_color}]"
        return border

    def card(self,
             *sections: Union[str, tuple[str, str]],
             min_width: Optional[int] = None,
             max_width: Optional[int] = None,
             border_style: Literal["single_line", "double_line"] = "single_line",
             topic_offest: int = 1,
             padding_left: int = 0,
             padding_right: int = 0,
             color: Optional[str] = None,
             header_color: Optional[str] = None,
             border_color: Optional[str] = None,
             **kwargs) -> None:
        """
        Prints a card with sections.

        :param sections: Sections to be printed. Each section can be a string or a tuple of (topic, string).
        :param min_width: Minimum width of the card (including borders). Default is None (no minimum).
        :param max_width: Maximum width of the card (including borders). Default is None (no maximum).
        :param border_style: Border style to be used. Default is "single_line".
        :param topic_offest: Offset for the topic. Default is 1.
        :param padding_left: Padding on the left side of each line.
        :param padding_right: Padding on the right side of each line.
        :param color: Color for the text inside the card.
        :param header_color: Color for the header text.
        :param border_color: Color for the border.
        :param kwargs: Additional parameters.
        :return: None
        """

        return super().card(*sections,
                            min_width=min_width,
                            max_width=max_width,
                            border_style=border_style,
                            topic_offest=topic_offest,
                            padding_left=padding_left,
                            padding_right=padding_right,
                            color=color,
                            header_color=header_color,
                            border_color=border_color,
                            **kwargs)

    def _get_exclamation_prefix(self,
                             content: Any,
                             brackets_style: Optional[str] = None,
                             prefix_color: Optional[str] = None,
                             prefix_content_color: Optional[str] = None,
                             prefix_brackets_color: Optional[str] = None,
                             **kwargs) -> tuple[str, str, str]:
        opening_bracket, content, closing_bracket = super()._get_exclamation_prefix(content=content,
                                                                                    brackets_style=brackets_style,
                                                                                    **kwargs)
        # escape square brackets
        if brackets_style == "square":
            opening_bracket = "\\" + opening_bracket

        if prefix_content_color is None:
            prefix_content_color = prefix_color
        if prefix_content_color is not None:
            content = f"[{prefix_content_color}]{content}[/{prefix_content_color}]"

        if prefix_brackets_color is None:
            prefix_brackets_color = prefix_color
        if prefix_brackets_color is not None:
            opening_bracket = f"[{prefix_brackets_color}]{opening_bracket}[/{prefix_brackets_color}]"
            closing_bracket = f"[{prefix_brackets_color}]{closing_bracket}[/{prefix_brackets_color}]"

        return opening_bracket, content, closing_bracket

    def exclamation(self,
                    *message: Any,
                    prefix: Any,
                    prefix_brackets_style: Optional[str] = None,
                    prefix_margin: Optional[int] = None,
                    color: Optional[str] = None,
                    message_color: Optional[str] = None,
                    prefix_color: Optional[str] = None,
                    prefix_content_color: Optional[str] = None,
                    prefix_brackets_color: Optional[str] = None,
                    **kwargs) -> None:
        """
        Prints an exclamation message.

        :param prefix: Prefix content.
        :param message: Main message content.
        :param prefix_brackets_style: Prefix bracket style. Default is class variable.
        :param prefix_margin: Margin on the right side of the prefix. Default is 1.
        :param color: Color for all parts. Can be overridden by specific colors. Default is None.
        :param message_color: Color for the main message. Default is color.
        :param prefix_color: Color for the prefix part. Default is color.
        :param prefix_content_color: Color for the prefix content. Default is prefix_color.
        :param prefix_brackets_color: Color for the prefix brackets. Default is prefix_color.
        :param kwargs: Additional parameters.
        :return: None
        """

        if message_color is None:
            message_color = color
        if message_color is not None:
            message = f"[{message_color}]{message}[/{message_color}]"

        if prefix_color is None:
            prefix_color = color

        return super().exclamation(*message,
                                   prefix=prefix,
                                   prefix_brackets_style=prefix_brackets_style,
                                   prefix_margin=prefix_margin,
                                   prefix_color=prefix_color,
                                   prefix_content_color=prefix_content_color,
                                   prefix_brackets_color=prefix_brackets_color,
                                   **kwargs)
