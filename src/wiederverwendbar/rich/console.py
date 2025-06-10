from typing import Optional, Literal, Union, Any

from rich.console import Console as _RichConsole

from wiederverwendbar.console.console import Console as _Console
from wiederverwendbar.console.out_files import OutFiles
from wiederverwendbar.rich.settings import RichConsoleSettings


class RichConsole(_Console, _RichConsole):
    print_function = _RichConsole.print
    print_function_blacklist_kwargs = _Console.print_function_blacklist_kwargs + ["color", "header_color", "border_color"]

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

    def _card_kwargs(self, mode: Literal["text", "header", "border", "print"], **kwargs) -> dict[str, Any]:
        out = super()._card_kwargs(mode=mode, **kwargs)
        for key in kwargs:
            if mode == "text":
                if key not in ["color"]:
                    continue
                out[key] = kwargs[key]
            elif mode == "header":
                if key not in ["header_color"]:
                    continue
                out[key] = kwargs[key]
            elif mode == "border":
                if key not in ["border_color"]:
                    continue
                out[key] = kwargs[key]
        return out

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
                         border_part: Literal["horizontal", "vertical", "top_left", "top_right", "bottom_left", "bottom_right", "vertical_left", "vertical_right"],
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
