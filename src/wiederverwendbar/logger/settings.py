import encodings
import logging
from pathlib import Path
from typing import Any, Optional, Union

from pydantic import field_validator

from wiederverwendbar.console import OutFiles
from wiederverwendbar.default import Default
from wiederverwendbar.logger.file_modes import FileModes
from wiederverwendbar.logger.log_levels import LogLevels
from wiederverwendbar.printable_settings import PrintableSettings, Field


class LoggerSettings(PrintableSettings):
    level: Union[Default, LogLevels] = Field(default=Default(), title="Log Level", description="The log level")
    console: bool = Field(default=True, title="Console Logging", description="Whether to log to the console")
    console_level: Union[Default, LogLevels] = Field(default=Default(), title="Console Log Level", description="The log level for the console")
    console_format: str = Field(default="%(name)s - %(message)s", title="Console Log Format", description="The log format for the console")
    console_width: int = Field(default=80, title="Console Width", ge=0, description="The width of the console")
    console_outfile: OutFiles = Field(default=OutFiles.STDOUT, title="Console Outfile", description="The console outfile")
    console_rich_markup: bool = Field(default=True, title="Rich Markup", description="Whether to use rich markup in the console")
    console_rich_show_time: bool = Field(default=False, title="Show Time in Console", description="Whether to show the time in the console")
    console_rich_show_level: bool = Field(default=True, title="Show Level in Console", description="Whether to show the level in the console")
    console_rich_show_path: bool = Field(default=True, title="Show Path in Console", description="Whether to show the path in the console")
    file: bool = Field(default=False, title="File Logging", description="Whether to log to a file")
    file_path: Optional[Path] = Field(default=None, title="Log File Path", description="The path of the log file")
    file_level: Union[Default, LogLevels] = Field(default=Default(), title="File Log Level", description="The log level for the file")
    file_format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", title="File Log Format", description="The log format for the file")
    file_mode: FileModes = Field(default=FileModes.a, title="File Mode", description="The file mode")
    file_max_bytes: int = Field(default=1024 * 1024 * 10, title="Max File Size", ge=1024, description="The maximum size of the log file. Default is 10MB")
    file_backup_count: int = Field(default=5, title="Backup Log Files", description="The number of backup log files to keep")
    file_encoding: str = Field(default="utf-8", title="File Encoding", description="The encoding of the log file")
    file_delay: bool = Field(default=False, title="Delay File Logging", description="Whether to delay the file logging")
    file_archive_backup_count: int = Field(default=5, title="Backup Log Archives", ge=0, description="The number of backup log archives to keep")

    def model_post_init(self, context: Any, /):
        if type(self.level) is Default:
            self.level = LogLevels.WARNING
        if type(self.console_level) is Default:
            self.console_level = self.level
        if type(self.file_level) is Default:
            self.file_level = self.level

        super().model_post_init(context)

    @field_validator("level", "console_level", "file_level", mode="before")
    def validate_level(cls, value: Union[int, str]) -> str:
        if isinstance(value, int):
            value = logging.getLevelName(value)
        return value

    @field_validator("file_encoding")
    def validate_file_encoding(cls, value):
        # check if encoding is available
        available_encodings = [encoding_name.replace("_", "-") for encoding_name in encodings.aliases.aliases.values()]
        if value not in available_encodings:
            raise ValueError(f"Encoding '{value}' is not available. Available encodings: {', '.join(available_encodings)}")
        return value
