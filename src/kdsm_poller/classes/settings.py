from wiederverwendbar.logger import LoggerSettings
from wiederverwendbar.pydantic.file_config import FileConfig
from wiederverwendbar.pydantic.indexable_model import IndexableModel
from wiederverwendbar.singleton import Singleton


class Settings(FileConfig, LoggerSettings, IndexableModel, metaclass=Singleton):
    # log
    log_ignored_loggers_equal: list[str] = []  # ["wiederverwendbar.before_after_wrap"]
    log_ignored_loggers_like: list[str] = []  # ["pymongo", "urllib3", "paramiko", "smbprotocol", "pypsexec"]
