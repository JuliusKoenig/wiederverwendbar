import logging

from wiederverwendbar.logger.logger import Logger
from wiederverwendbar.logger.logger_settings import LoggerSettings
from wiederverwendbar.singleton import Singleton

LOGGER_SINGLETON_ORDER = 10


class LoggerSingleton(Logger, metaclass=Singleton, order=LOGGER_SINGLETON_ORDER):
    def __init__(self, name: str,
                 settings: LoggerSettings,
                 use_sub_logger: bool = True,
                 ignored_loggers_equal: list[str] = None,
                 ignored_loggers_like: list[str] = None):
        if ignored_loggers_equal is None:
            ignored_loggers_equal = []
        if ignored_loggers_like is None:
            ignored_loggers_like = []

        super().__init__(name, settings)

        if use_sub_logger:
            logging.setLoggerClass(SubLogger)

        self.ignored_loggers_equal = ignored_loggers_equal
        self.ignored_loggers_like = ignored_loggers_like


class SubLogger(logging.Logger):
    def __init__(self, name: str, level=logging.NOTSET):
        self.init = False
        logger_singleton = LoggerSingleton()

        if name in logger_singleton.ignored_loggers_equal:
            super().__init__(name, level)
        elif any([ignored in name for ignored in logger_singleton.ignored_loggers_like]):
            super().__init__(name, level)
        else:
            super().__init__(name, level)

            self.parent = logger_singleton

            self.init = True

    def __setattr__(self, key, value):
        if key == "init":
            return super().__setattr__(key, value)
        if not self.init:
            return super().__setattr__(key, value)

    def setLevel(self, level):
        if not self.init:
            return super().setLevel(level)

    def addHandler(self, hdlr):
        if not self.init:
            return super().addHandler(hdlr)

    def removeHandler(self, hdlr):
        if not self.init:
            return super().removeHandler(hdlr)

    def addFilter(self, fltr):
        if not self.init:
            return super().addFilter(fltr)

    def removeFilter(self, fltr):
        if not self.init:
            return super().removeFilter(fltr)
