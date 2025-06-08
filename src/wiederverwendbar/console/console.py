import sys
from abc import ABC, abstractmethod
from typing import Optional, Any

from wiederverwendbar.console.out_files import OutFiles
from wiederverwendbar.console.settings import ConsoleSettings

class BaseConsole(ABC):
    @abstractmethod
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


class Console(BaseConsole):
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
        self.console_file = console_file
        if console_seperator is None:
            console_seperator = settings.console_seperator
        self.console_seperator = console_seperator
        if console_end is None:
            console_end = settings.console_end
        self.console_end = console_end

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
        if self.console_file == OutFiles.STDOUT:
            print(*args, sep=sep, end=end, file=sys.stdout, **kwargs)
        elif self.console_file == OutFiles.STDERR:
            print(*args, sep=sep, end=end, file=sys.stderr, **kwargs)
        else:
            raise ValueError(f"Unknown console file '{self.console_file}'.")
