from typing import Optional

from rich.logging import RichHandler

from wiederverwendbar.console.out_files import OutFiles
from wiederverwendbar.rich.console import RichConsole


class RichConsoleHandler(RichHandler):
    def __init__(self,
                 *args,
                 name: str,
                 console: Optional[RichConsole] = None,
                 console_outfile: Optional[OutFiles] = None,
                 console_width: Optional[int] = None,
                 **kwargs):
        if console is None:
            console = RichConsole(console_file=console_outfile,
                                  console_width=console_width)
        super().__init__(
            *args,
            console=console,
            **kwargs
        )
        self.set_name(name)
