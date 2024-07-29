from rich.console import Console
from rich.logging import RichHandler

from wiederverwendbar.logger.handlers.stream_console_handler import _resolve_file
from wiederverwendbar.logger.settings import LoggerSettings


class RichConsoleHandler(RichHandler):
    def __init__(self, *args, name: str, console_outfile: LoggerSettings.TerminalOutFile, console_width: int, **kwargs):
        super().__init__(
            *args,
            console=Console(file=_resolve_file(console_outfile),
                            width=console_width),
            **kwargs
        )
        self.set_name(name)
