import logging

from wiederverwendbar.logger.handlers import RichConsoleHandler, StreamConsoleHandler, TarRotatingFileHandler
from wiederverwendbar.logger.settings import LoggerSettings


class Logger(logging.Logger):
    def __init__(self, name: str, settings: LoggerSettings):
        super().__init__(name)

        self.settings = settings

        # set log level
        self.setLevel(self.settings.level.value)

        # add null handler
        null_handler = logging.NullHandler()
        self.addHandler(null_handler)

        # add console handler
        if self.settings.console:
            if RichConsoleHandler is None:
                ch = StreamConsoleHandler(
                    name=name,
                    console_outfile=self.settings.console_outfile
                )
            else:
                ch = RichConsoleHandler(
                    name=name,
                    console_outfile=self.settings.console_outfile,
                    console_width=self.settings.console_width,
                    show_time=self.settings.console_rich_show_time,
                    markup=self.settings.console_rich_markup,
                    show_level=self.settings.console_rich_show_level,
                    show_path=self.settings.console_rich_show_path
                )
            if self.settings.console_level is not None:
                ch.setLevel(self.settings.console_level.value)
            ch.setFormatter(logging.Formatter(self.settings.console_format))
            self.addHandler(ch)

        # add file handler
        if self.settings.file:
            # check if log_file_path is set
            if self.settings.file_path is None:
                raise ValueError("Log file path not set")

            # check if log_file_path parent directory exists
            if not self.settings.file_path.parent.exists():
                raise FileNotFoundError(f"Log file path parent directory not exist: '{self.settings.file_path.parent}'")

            fh = TarRotatingFileHandler(
                name=name,
                filename=self.settings.file_path,
                mode=self.settings.file_mode,
                max_bytes=self.settings.file_max_bytes,
                backup_count=self.settings.file_backup_count,
                encoding=self.settings.file_encoding,
                delay=self.settings.file_delay,
                archive_backup_count=self.settings.file_archive_backup_count
            )
            if self.settings.file_level is not None:
                fh.setLevel(self.settings.file_level.value)
            fh.setFormatter(logging.Formatter(self.settings.file_format))
            self.addHandler(fh)

        # log first message
        self.debug(f"Logger '{name}' initialized.")
