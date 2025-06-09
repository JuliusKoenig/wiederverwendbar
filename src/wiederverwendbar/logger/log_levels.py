import logging
from enum import Enum


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

    def get_level_number(self) -> int:
        return int(logging.getLevelName(self.value))
