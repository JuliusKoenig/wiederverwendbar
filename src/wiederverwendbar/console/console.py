from typing import Optional, Any, Literal, Union

from wiederverwendbar.console.out_files import OutFiles
from wiederverwendbar.console.settings import ConsoleSettings


class Console:
    print_function = print
    print_function_blacklist_kwargs = ["file"]
    console_border_styles = {
        "single_line": ["─", "│", "┌", "┐", "└", "┘", "├", "┤"],
        "double_line": ["═", "║", "╔", "╗", "╚", "╝", "╠", "╣"]
    }

    def __init__(self,
                 *,
                 console_file: Optional[OutFiles] = None,
                 console_seperator: Optional[str] = None,
                 console_end: Optional[str] = None,
                 settings: Optional[ConsoleSettings] = None):
        """
        Create a new console.

        :param console_file: Console file. Default is STDOUT.
        :param console_seperator: Console seperator. Default is a space.
        :param console_end: Console end. Default is a newline.
        :param settings: A settings object to use. If None, defaults to ConsoleSettings().
        """

        if settings is None:
            settings = ConsoleSettings()

        if console_file is None:
            console_file = settings.console_file
        self._console_file = console_file

        if console_seperator is None:
            console_seperator = settings.console_seperator
        self._console_seperator = console_seperator

        if console_end is None:
            console_end = settings.console_end
        self._console_end = console_end

    def _print_method_kwargs_filter(self, **kwargs) -> dict[str, Any]:
        for key in kwargs.copy():
            if key not in self.print_function_blacklist_kwargs:
                continue
            del kwargs[key]
        return kwargs

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
            sep = self._console_seperator
        if end is None:
            end = self._console_end
        self.print_function(*args, **self._print_method_kwargs_filter(sep=sep, end=end, file=OutFiles.STDOUT.get_file(), **kwargs))

    def _card_kwargs(self, mode: Literal["text", "header", "border", "print"], **kwargs) -> dict[str, Any]:
        return {}

    def _card_get_text(self, text: str, **kwargs) -> str:
        return text

    def _card_get_header_text(self, text: str, **kwargs) -> str:
        return text

    def _card_get_border(self,
                         border_style: Literal["single_line", "double_line"],
                         border_part: Literal["horizontal", "vertical", "top_left", "top_right", "bottom_left", "bottom_right", "vertical_left", "vertical_right"],
                         **kwargs):
        border_style = self.console_border_styles[border_style]
        if border_part == "horizontal":
            return border_style[0]
        elif border_part == "vertical":
            return border_style[1]
        elif border_part == "top_left":
            return border_style[2]
        elif border_part == "top_right":
            return border_style[3]
        elif border_part == "bottom_left":
            return border_style[4]
        elif border_part == "bottom_right":
            return border_style[5]
        elif border_part == "vertical_left":
            return border_style[6]
        elif border_part == "vertical_right":
            return border_style[7]
        else:
            raise ValueError(f"Unknown border part '{border_part}'.")

    def card(self,
             *sections: Union[str, tuple[str, str]],
             min_width: Optional[int] = None,
             max_width: Optional[int] = None,
             border_style: Literal["single_line", "double_line"] = "single_line",
             topic_offest: int = 1,
             padding_left: int = 0,
             padding_right: int = 0,
             **kwargs) -> None:
        if min_width and max_width and min_width > max_width:
            raise ValueError(f"min_width '{min_width}' is greater than max_width '{max_width}'.")
        if min_width is not None:
            min_width -= 2
        if max_width is not None:
            if max_width < 10:
                raise ValueError(f"max_width '{max_width}' is smaller than 10.")
            max_width -= 2

        # get real width
        real_width = 0
        if min_width is not None:
            real_width = min_width
        for section in sections:
            section_topic = ""
            if isinstance(section, tuple):
                section_topic = section[0]
                section = section[1]

            # update real with
            if len(section_topic) + topic_offest > real_width:
                real_width = len(section_topic) + topic_offest

            for line in section.splitlines():
                line = " " * padding_left + line + " " * padding_right  # add padding
                # update real with
                if len(line) > real_width:
                    real_width = len(line)
        if max_width is not None:
            if real_width > max_width:
                real_width = max_width

        # format sections
        section_topics: list[str] = []
        formatted_sections: list[list[str]] = []
        for section in sections:
            section_topic = ""
            if isinstance(section, tuple):
                section_topic = section[0]
                section = section[1]
            if section_topic != "":
                section_topic = " " + section_topic + " "

            # topic max width
            if len(section_topic) + topic_offest > real_width:
                section_topic = section_topic[:real_width - topic_offest - 3] + "..."

            section_topics.append(section_topic)
            formatted_lines: list[str] = []
            lines = section.splitlines()
            while len(lines) > 0:
                line = lines.pop(0)

                # add topic
                line = " " * padding_left + line  # add padding

                # max width
                if len(line) + padding_right > real_width:
                    lines.insert(0, line[real_width - padding_right:])
                    line = line[:real_width - padding_right] + " " * padding_right
                else:
                    line = line.ljust(real_width - padding_right) + " " * padding_right

                formatted_lines.append(line)
            formatted_sections.append(formatted_lines)
        card = (f"{self._card_get_border(border_style, 'top_left', **kwargs)}"
                f"{self._card_get_border(border_style, 'horizontal', **kwargs) * topic_offest}"
                f"{self._card_get_header_text(section_topics[0], **kwargs)}"
                f"{self._card_get_border(border_style, 'horizontal', **kwargs) * (real_width - len(section_topics.pop(0)) - topic_offest)}"
                f"{self._card_get_border(border_style, 'top_right', **kwargs)}\n")
        while len(formatted_sections) > 0:
            for line in formatted_sections.pop(0):
                card += (f"{self._card_get_border(border_style, 'vertical', **kwargs)}"
                         f"{self._card_get_text(line, **kwargs)}"
                         f"{self._card_get_border(border_style, 'vertical', **kwargs)}\n")
            if len(formatted_sections) > 0:
                card += (f"{self._card_get_border(border_style, 'vertical_left', **kwargs)}"
                         f"{self._card_get_border(border_style, 'horizontal', **kwargs) * topic_offest}"
                         f"{self._card_get_header_text(section_topics[0], **kwargs)}"
                         f"{self._card_get_border(border_style, 'horizontal', **kwargs) * (real_width - len(section_topics.pop(0)) - topic_offest)}"
                         f"{self._card_get_border(border_style, 'vertical_right', **kwargs)}\n")
            else:
                card += (f"{self._card_get_border(border_style, 'bottom_left', **kwargs)}"
                         f"{self._card_get_border(border_style, 'horizontal', **kwargs) * real_width}"
                         f"{self._card_get_border(border_style, 'bottom_right', **kwargs)}")
        return self.print(card, **kwargs)
