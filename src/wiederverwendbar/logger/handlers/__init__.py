from wiederverwendbar.logger.handlers.stream_console_handler import StreamConsoleHandler

try:
    from wiederverwendbar.logger.handlers.rich_console_handler import RichConsoleHandler
except ModuleNotFoundError:
    RichConsoleHandler = None

from wiederverwendbar.logger.handlers.tar_rotating_file_handler import TarRotatingFileHandler
