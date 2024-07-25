import logging
from typing import Any

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
            self.configure()

    def configure(self):
        for logger in logging.Logger.manager.loggerDict.values():
            if not isinstance(logger, logging.Logger):
                continue
            self.configure_logger(logger)

    def configure_logger(self, logger: logging.Logger):
        if logger.name in self.ignored_loggers_equal or any([ignored in logger.name for ignored in self.ignored_loggers_like]):
            if isinstance(logger, SubLogger):
                logger.configure()
            return
        logger.setLevel(self.level)
        logger.parent = self


class SubLogger(logging.Logger):
    def __init__(self, name: str, level=logging.NOTSET):
        self.init = True
        self._configure_log: list[tuple[callable, dict[str, Any]]] = []
        self.init = False
        super().__init__(name, level)
        LoggerSingleton().configure_logger(self)
        self.init = True

    def __setattr__(self, key, value):
        if key in ["init", "_configure_log"]:
            return super().__setattr__(key, value)
        if not self.init:
            return super().__setattr__(key, value)
        self._configure_log.append((self.__setattr__, {"key": key, "value": value}))

    def configure(self):
        for func, kwargs in self._configure_log:
            func(**kwargs)
        self._configure_log = []

    def setLevel(self, level):
        if not self.init:
            return super().setLevel(level)
        self._configure_log.append((self.setLevel, {"level": level}))

    def addHandler(self, hdlr):
        if not self.init:
            return super().addHandler(hdlr)
        self._configure_log.append((self.addHandler, {"hdlr": hdlr}))

    def removeHandler(self, hdlr):
        if not self.init:
            return super().removeHandler(hdlr)
        self._configure_log.append((self.removeHandler, {"hdlr": hdlr}))

    def addFilter(self, fltr):
        if not self.init:
            return super().addFilter(fltr)
        self._configure_log.append((self.addFilter, {"fltr": fltr}))

    def removeFilter(self, fltr):
        if not self.init:
            return super().removeFilter(fltr)
        self._configure_log.append((self.removeFilter, {"fltr": fltr}))
