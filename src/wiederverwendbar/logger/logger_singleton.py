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

        self.ignored_loggers_equal = ignored_loggers_equal
        self.ignored_loggers_like = ignored_loggers_like

        if use_sub_logger:
            logging.setLoggerClass(SubLogger)

            for logger in logging.Logger.manager.loggerDict.values():
                if not isinstance(logger, logging.Logger):
                    continue
                _configure_logger(logger)


def _configure_logger(cls: logging.Logger):
    logger_singleton = LoggerSingleton()
    if cls.name in logger_singleton.ignored_loggers_equal or any([ignored in cls.name for ignored in logger_singleton.ignored_loggers_like]):
        return
    cls.setLevel(logger_singleton.level)
    cls.parent = logger_singleton


class SubLogger(logging.Logger):
    def __init__(self, name: str, level=logging.NOTSET):
        self.init = False
        super().__init__(name, level)
        _configure_logger(self)
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
