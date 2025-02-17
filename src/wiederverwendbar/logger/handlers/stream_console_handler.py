import logging
import sys

from wiederverwendbar.logger.terminal_out_files import TerminalOutFiles


def _resolve_file(outfile: TerminalOutFiles):
    # choose file
    if outfile == TerminalOutFiles.STDOUT:
        file = sys.stdout
    elif outfile == TerminalOutFiles.STDERR:
        file = sys.stderr
    else:
        file = sys.stderr

    return file


class StreamConsoleHandler(logging.StreamHandler):
    def __init__(self, name: str, console_outfile: TerminalOutFiles):
        super().__init__(stream=_resolve_file(console_outfile))
        self.set_name(name)
