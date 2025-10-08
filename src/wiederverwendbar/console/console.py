from typing import Optional, Any, Literal, Union, IO

from wiederverwendbar.console.out_files import OutFilesLiteral, OutFiles
from wiederverwendbar.console.settings import ConsoleSettings


class Console:
    print_function = print
    console_border_styles = {
        "single_line": ["─", "│", "┌", "┐", "└", "┘", "├", "┤"],
        "double_line": ["═", "║", "╔", "╗", "╚", "╝", "╠", "╣"]
    }
    console_exclamation_bracket_styles = {
        "square": ["[", "]"],
        "round": ["(", ")"],
        "curly": ["{", "}"],
        "angle": ["<", ">"],
        "none": ["", ""]
    }
    console_exclamation_message_templates = {
        "trace": {
            "prefix": "TRACE",
            "prefix_margin": 4
        },
        "debug": {
            "prefix": "DEBUG",
            "prefix_margin": 4
        },
        "info": {
            "prefix": "INFO",
            "prefix_margin": 5
        },
        "warning": {
            "prefix": "WARNING",
            "prefix_margin": 2
        },
        "error": {
            "prefix": "ERROR",
            "prefix_margin": 4
        },
        "critical": {
            "prefix": "CRITICAL",
            "prefix_margin": 1
        },
        "panic": {
            "prefix": "PANIC",
            "prefix_margin": 4
        },
        "okay": {
            "prefix": "OKAY",
            "prefix_margin": 5
        },
        "success": {
            "prefix": "SUCCESS",
            "prefix_margin": 2
        },
        "fail": {
            "prefix": "FAIL",
            "prefix_margin": 5
        }
    }

    def __init__(self,
                 *,
                 console_file: Optional[OutFiles] = None,
                 console_seperator: Optional[str] = None,
                 console_end: Optional[str] = None,
                 console_exclamation_prefix_brackets_style: Optional[str] = None,
                 settings: Optional[ConsoleSettings] = None):
        """
        Create a new console.

        :param console_file: Console file. Default is STDOUT.
        :param console_seperator: Console seperator. Default is a space.
        :param console_end: Console end. Default is a newline.
        :param console_exclamation_prefix_brackets_style: Console exclamation bracket style. Default is "square".
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

        if console_exclamation_prefix_brackets_style is None:
            console_exclamation_prefix_brackets_style = settings.console_exclamation_prefix_brackets_style
        self._console_exclamation_prefix_brackets_style = console_exclamation_prefix_brackets_style

    def print(self,
              *args: Any,
              sep: Optional[str] = None,
              end: Optional[str] = None,
              file: Union[None, OutFilesLiteral, OutFiles, IO] = None,
              **kwargs) -> None:
        """
        Prints the values.

        :param args: values to be printed.
        :param sep:  string inserted between values, Default is class variable.
        :param end:  string appended after the last value, Default is class variable.
        :param file: Output file. Default is class variable.
        :param kwargs: Additional parameters.
        """

        if sep is None:
            sep = self._console_seperator
        if end is None:
            end = self._console_end
        if file is None:
            file = self._console_file
        if type(file) is str:
            file = OutFiles(file)
        if isinstance(file, OutFiles):
            file = file.get_file()

        self.print_function(*args, sep=sep, end=end, file=file, **kwargs)

    def _card_get_text(self, text: str, **kwargs) -> str:
        return text

    def _card_get_header_text(self, text: str, **kwargs) -> str:
        return text

    def _card_get_border(self,
                         border_style: Literal["single_line", "double_line"],
                         border_part: Literal[
                             "horizontal", "vertical", "top_left", "top_right", "bottom_left", "bottom_right", "vertical_left", "vertical_right"],
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
        """
        Prints a card with sections.

        :param sections: Sections to be printed. Each section can be a string or a tuple of (topic, string).
        :param min_width: Minimum width of the card (including borders). Default is None (no minimum).
        :param max_width: Maximum width of the card (including borders). Default is None (no maximum).
        :param border_style: Border style to be used. Default is "single_line".
        :param topic_offest: Offset for the topic. Default is 1.
        :param padding_left: Padding on the left side of each line.
        :param padding_right: Padding on the right side of each line.
        :param kwargs: Additional parameters.
        :return: None
        """

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

    def _get_exclamation_prefix(self,
                                content: Any,
                                *,
                                prefix_brackets_style: Optional[str] = None,
                                **kwargs) -> tuple[str, str, str]:
        return (self.console_exclamation_bracket_styles[prefix_brackets_style][0],
                str(content),
                self.console_exclamation_bracket_styles[prefix_brackets_style][1])

    def exclamation(self,
                    *message: Any,
                    prefix: Any,
                    prefix_brackets_style: Optional[str] = None,
                    prefix_margin: Optional[int] = None,
                    **kwargs) -> None:
        """
        Prints an exclamation message.

        :param message: Main message content.
        :param prefix: Prefix content.
        :param prefix_brackets_style: Prefix bracket style. Default is class variable.
        :param prefix_margin: Margin on the right side of the prefix. Default is 1.
        :param kwargs: Additional parameters.
        :return: None
        """

        if prefix_brackets_style is None:
            prefix_brackets_style = self._console_exclamation_prefix_brackets_style
        if prefix_margin is None:
            prefix_margin = 1

        def get_prefix_kwargs(f: str, **kw) -> dict[str, Any]:
            for key in kwargs.copy():
                if not key.startswith(f):
                    continue
                kw[key] = kwargs[key]
                del kwargs[key]
            return kw

        prefix_kwargs = get_prefix_kwargs("prefix_", content=prefix, prefix_brackets_style=prefix_brackets_style)
        prefix_parts = self._get_exclamation_prefix(**prefix_kwargs)
        exclamation = f"{prefix_parts[0]}{prefix_parts[1]}{prefix_parts[2]}{' ' * prefix_margin}"
        first = True
        for line in message:
            if not first:
                exclamation += "\n  "
            exclamation += line
            first = False
        return self.print(exclamation, **kwargs)

    trace = lambda self, *message, **kwargs: self.exclamation(*message,
                                                             **{**self.console_exclamation_message_templates["trace"],
                                                                **kwargs})
    debug = lambda self, *message, **kwargs: self.exclamation(*message,
                                                             **{**self.console_exclamation_message_templates["debug"],
                                                                **kwargs})
    info = lambda self, *message, **kwargs: self.exclamation(*message,
                                                            **{**self.console_exclamation_message_templates["info"],
                                                               **kwargs})
    warning = lambda self, *message, **kwargs: self.exclamation(*message,
                                                               **{**self.console_exclamation_message_templates[
                                                                   "warning"],
                                                                  **kwargs})
    error = lambda self, *message, **kwargs: self.exclamation(*message,
                                                             **{**self.console_exclamation_message_templates["error"],
                                                                **kwargs})
    critical = lambda self, *message, **kwargs: self.exclamation(*message,
                                                                **{**self.console_exclamation_message_templates[
                                                                    "critical"],
                                                                   **kwargs})
    panic = lambda self, *message, **kwargs: self.exclamation(*message,
                                                             **{**self.console_exclamation_message_templates["panic"],
                                                                **kwargs})
    okay = lambda self, *message, **kwargs: self.exclamation(*message,
                                                            **{**self.console_exclamation_message_templates["okay"],
                                                               **kwargs})
    success = lambda self, *message, **kwargs: self.exclamation(*message,
                                                               **{**self.console_exclamation_message_templates[
                                                                   "success"],
                                                                  **kwargs})
    fail = lambda self, *message, **kwargs: self.exclamation(*message,
                                                            **{**self.console_exclamation_message_templates["fail"],
                                                               **kwargs})
