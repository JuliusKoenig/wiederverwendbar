import logging

from wiederverwendbar.logger.handlers import RichConsoleHandler, StreamConsoleHandler, TarRotatingFileHandler
from wiederverwendbar.logger.settings import LoggerSettings


class Logger(logging.Logger):
    def __init__(self, name: str, settings: LoggerSettings):
        super().__init__(name, level=logging.DEBUG)

        self.settings = settings

        # add null handler
        null_handler = logging.NullHandler()
        self.addHandler(null_handler)

        # add console handler
        if self.settings.log_console:
            if RichConsoleHandler is None:
                ch = StreamConsoleHandler(
                    name=name,
                    console_outfile=self.settings.log_console_outfile
                )
            else:
                ch = RichConsoleHandler(
                    name=name,
                    console_outfile=self.settings.log_console_outfile,
                    console_width=self.settings.log_console_width,
                    show_time=self.settings.log_console_rich_show_time,
                    markup=self.settings.log_console_rich_markup,
                    show_level=self.settings.log_console_rich_show_level,
                    show_path=self.settings.log_console_rich_show_path
                )
            if self.settings.log_console_level is not None:
                ch.setLevel(self.settings.log_console_level.value)
            ch.setFormatter(logging.Formatter(self.settings.log_console_format))
            self.addHandler(ch)

        # add file handler
        if self.settings.log_file:
            # check if log_file_path is set
            if self.settings.log_file_path is None:
                raise ValueError("Log file path not set")

            # check if log_file_path parent directory exists
            if not self.settings.log_file_path.parent.exists():
                raise FileNotFoundError(f"Log file path parent directory not exist: '{self.settings.log_file_path.parent}'")

            fh = TarRotatingFileHandler(
                name=name,
                filename=self.settings.log_file_path,
                mode=self.settings.log_file_mode,
                max_bytes=self.settings.log_file_max_bytes,
                backup_count=self.settings.log_file_backup_count,
                encoding=self.settings.log_file_encoding,
                delay=self.settings.log_file_delay,
                archive_backup_count=self.settings.log_file_archive_backup_count
            )
            if self.settings.log_file_level is not None:
                fh.setLevel(self.settings.log_file_level.value)
            fh.setFormatter(logging.Formatter(self.settings.log_file_format))
            self.addHandler(fh)

        # log first message
        self.debug(f"Logger '{name}' initialized.")
