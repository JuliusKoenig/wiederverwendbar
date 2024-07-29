import logging
import sys

from wiederverwendbar.logger import LoggingContext
from wiederverwendbar.logger import LoggerSingleton, LoggerSettings

from wiederverwendbar.examples.logger_context.example_module import example_function

LoggerSingleton(init=True, name="test", settings=LoggerSettings(log_level="DEBUG"), ignored_loggers_like=["logger1", "logger2"])

logger1 = logging.getLogger("logger1")
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter('logger1 - %(name)s - %(levelname)s - %(message)s'))
logger1.addHandler(ch)
logger1.setLevel(logging.DEBUG)

logger2 = logging.getLogger("logger2")
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter('logger2 - %(name)s - %(levelname)s - %(message)s'))
logger2.addHandler(ch)
logger2.setLevel(logging.DEBUG)

if __name__ == '__main__':
    # no context
    logger1.debug("no context")
    logger2.debug("no context")

    with LoggingContext(logger1, handle_origin_logger=False) as context1_a:
        with LoggingContext(logger2, handle_origin_logger=False) as context2_a:
            example_function()
        example_function()
    example_function()

    with LoggingContext(logger1, handle_origin_logger=False) as context1_b:
        with LoggingContext(logger2, handle_origin_logger=False) as context2_b:
            example_function()
        example_function()
    example_function()

    # again no context
    logger1.debug("again no context")
    logger2.debug("again no context")

    sys.exit(0)
