import encodings
import logging
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union

from pydantic import BaseModel, Field, field_validator


class LoggerSettings(BaseModel):
    class LogLevels(str, Enum):
        """
        Log levels
        """

        CRITICAL = "CRITICAL"
        FATAL = "FATAL"
        ERROR = "ERROR"
        WARNING = "WARNING"
        INFO = "INFO"
        DEBUG = "DEBUG"

    log_level: LogLevels = Field(default=LogLevels.WARNING,
                                 title="Log Level",
                                 description="The log level")

    log_console: bool = Field(default=True,
                              title="Console Logging",
                              description="Whether to log to the console")
    log_console_level: Optional[LogLevels] = Field(default=None,
                                                   title="Console Log Level",
                                                   description="The log level for the console")
    log_console_format: str = Field(default="%(name)s - %(message)s",
                                    title="Console Log Format",
                                    description="The log format for the console")
    log_console_width: int = Field(default=80,
                                   title="Console Width",
                                   ge=0,
                                   description="The width of the console")

    class TerminalOutFile(str, Enum):
        """
        Terminal output file
        """

        STDOUT = "stdout"
        STDERR = "stderr"

    log_console_outfile: TerminalOutFile = Field(default=TerminalOutFile.STDOUT,
                                                 title="Console Outfile",
                                                 description="The console outfile")
    log_console_rich_markup: bool = Field(default=True,
                                          title="Rich Markup",
                                          description="Whether to use rich markup in the console")
    log_console_rich_show_time: bool = Field(default=False,
                                             title="Show Time in Console",
                                             description="Whether to show the time in the console")
    log_console_rich_show_level: bool = Field(default=True,
                                              title="Show Level in Console",
                                              description="Whether to show the level in the console")
    log_console_rich_show_path: bool = Field(default=True,
                                             title="Show Path in Console",
                                             description="Whether to show the path in the console")
    log_file: bool = Field(default=False,
                           title="File Logging",
                           description="Whether to log to a file")
    log_file_path: Optional[Path] = Field(default=None,
                                          title="Log File Path",
                                          description="The path of the log file")
    log_file_level: Optional[LogLevels] = Field(default=None,
                                                title="File Log Level",
                                                description="The log level for the file")
    log_file_format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                                 title="File Log Format",
                                 description="The log format for the file")

    class FileMode(str, Enum):
        """
        File mode
        """

        a = "a"
        w = "w"

    log_file_mode: FileMode = Field(default=FileMode.a,
                                    title="File Mode",
                                    description="The file mode")
    log_file_max_bytes: int = Field(default=1024 * 1024 * 10,
                                    title="Max File Size",
                                    ge=1024,
                                    description="The maximum size of the log file. Default is 10MB")
    log_file_backup_count: int = Field(default=5,
                                       title="Backup Log Files",
                                       description="The number of backup log files to keep")
    log_file_encoding: str = Field(default="utf-8",
                                   title="File Encoding",
                                   description="The encoding of the log file")

    log_file_delay: bool = Field(default=False,
                                 title="Delay File Logging",
                                 description="Whether to delay the file logging")
    log_file_archive_backup_count: int = Field(default=5,
                                               title="Backup Log Archives",
                                               ge=0,
                                               description="The number of backup log archives to keep")

    def __init__(self, /, **data: Any):
        super().__init__(**data)

        if self.log_console_level is None:
            self.log_console_level = self.log_level

        if self.log_file_level is None:
            self.log_file_level = self.log_level

    @field_validator("log_level", "log_console_level", "log_file_level", mode="before")
    def validate_log_level(cls, value: Union[int, str]) -> str:
        if isinstance(value, int):
            value = logging.getLevelName(value)
        return value

    @field_validator("log_file_encoding")
    def validate_log_file_encoding(cls, value):
        # check if encoding is available
        available_encodings = [encoding_name.replace("_", "-") for encoding_name in encodings.aliases.aliases.values()]
        if value not in available_encodings:
            raise ValueError(f"Encoding '{value}' is not available. Available encodings: {', '.join(available_encodings)}")
        return value
