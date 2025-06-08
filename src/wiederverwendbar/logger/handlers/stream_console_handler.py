import logging

from wiederverwendbar.console import OutFiles


class StreamConsoleHandler(logging.StreamHandler):
    def __init__(self, name: str, console_outfile: OutFiles):
        super().__init__(stream=console_outfile.get_file())
        self.set_name(name)
