from wiederverwendbar.logger import LoggerSingleton

from kdsm_poller.classes.settings import Settings

__version__ = "0.1.0"
TITLE = "kdsm-poller"
VERSION = __version__
AUTHOR = "Kirchhoff Datensysteme Services GmbH & Co. KG - Julius Koenig"
AUTHOR_EMAIL = "julius.koenig@kds-kg.de"
LICENSE = "GPL-3.0"

# init settings
Settings(file_path="settings.json",
         log_level="DEBUG",
         init=True)

# init logger
logger = LoggerSingleton(name="kdsm-poller",
                         settings=Settings(),
                         ignored_loggers_equal=Settings().log_ignored_loggers_equal,
                         ignored_loggers_like=Settings().log_ignored_loggers_like,
                         init=True)
