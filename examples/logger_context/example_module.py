import logging
import time

logger = logging.getLogger(__name__)


def example_function():
    logger.debug("example_function")
    func_logger = logging.getLogger(__name__ + ".example_function")
    time.sleep(1)
    func_logger.debug("debug")
    time.sleep(1)
    return
