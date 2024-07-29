import logging

logger = logging.getLogger(__name__)


def example_function():
    logger.debug("example_function")
    func_logger = logging.getLogger(__name__ + ".example_function")
    func_logger.debug("debug")
    return
