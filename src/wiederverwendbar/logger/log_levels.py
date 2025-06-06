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

    @property
    def logging_level(self) -> int:
        return getattr(logging, self.value)
