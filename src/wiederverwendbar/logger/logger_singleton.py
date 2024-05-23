from wiederverwendbar.logger.logger import Logger
from wiederverwendbar.singleton import Singleton

LOGGER_SINGLETON_ORDER = 10


class LoggerSingleton(Logger, metaclass=Singleton, order=LOGGER_SINGLETON_ORDER):
    ...
