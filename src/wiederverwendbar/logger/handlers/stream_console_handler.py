import logging
import sys

from wiederverwendbar.logger.settings import LoggerSettings


def _resolve_file(outfile: LoggerSettings.TerminalOutFile):
    # choose file
    if outfile == LoggerSettings.TerminalOutFile.STDOUT:
        file = sys.stdout
    elif outfile == LoggerSettings.TerminalOutFile.STDERR:
        file = sys.stderr
    else:
        file = sys.stderr

    return file


class StreamConsoleHandler(logging.StreamHandler):
    def __init__(self, name: str, console_outfile: LoggerSettings.TerminalOutFile):
        super().__init__(stream=_resolve_file(console_outfile))
        self.set_name(name)
