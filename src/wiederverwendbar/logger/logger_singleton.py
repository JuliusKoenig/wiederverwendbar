from wiederverwendbar.logger.logger import Logger
from wiederverwendbar.singleton import Singleton


class LoggerSingleton(Logger, metaclass=Singleton):
    ...
