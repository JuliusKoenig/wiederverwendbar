import contextlib
import logging

from wiederverwendbar.logger.logger import Logger
from wiederverwendbar.logger.settings import LoggerSettings
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

    def is_ignored(self, logger_name: str) -> bool:
        return logger_name in self.ignored_loggers_equal or any([ignored in logger_name for ignored in self.ignored_loggers_like])

    def configure(self):
        for logger in logging.Logger.manager.loggerDict.values():
            if not isinstance(logger, logging.Logger):
                continue
            self.configure_logger(logger)

    def configure_logger(self, logger: logging.Logger):
        if self.is_ignored(logger.name):
            return
        logger.setLevel(self.level)
        logger.parent = self


class SubLogger(logging.Logger):
    def __init__(self, name: str, level=logging.NOTSET):
        self._init = False
        super().__init__(name, level)
        LoggerSingleton().configure_logger(self)
        self._init = True

    def __setattr__(self, key, value):
        if key in ["_init" "init", "_configure_log"]:
            return super().__setattr__(key, value)
        if not self.init:
            return super().__setattr__(key, value)

    @property
    def init(self):
        if hasattr(self, "name"):
            if LoggerSingleton().is_ignored(self.name):
                return False
        return getattr(self, "_init", False)

    @contextlib.contextmanager
    def reconfigure(self):
        if self.init:
            try:
                super().__setattr__("_init", False)
                yield self
            finally:
                super().__setattr__("_init", True)
        else:
            yield self

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

    @classmethod
    def get_logger(cls, name: str) -> "SubLogger":
        logger = logging.getLogger(name)
        if not isinstance(logger, SubLogger):
            raise RuntimeError(f"Logger '{name}' is not a {cls.__name__}")
        return logger
