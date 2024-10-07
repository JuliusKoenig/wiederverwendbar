import logging
from typing import Union


def logger_exists(logger_or_name: Union[str, logging.Logger]) -> bool:
    """
    Check if logger exists.

    :param logger_or_name: Logger or name of logger to check.
    :return: True if logger exists, False otherwise.
    """

    if isinstance(logger_or_name, logging.Logger):
        logger_name = logger_or_name.name
    elif isinstance(logger_or_name, str):
        logger_name = logger_or_name
    else:
        raise TypeError(f"Expected 'str' or 'logging.Logger', got '{type(logger_or_name)}'.")
    return logger_name in logging.root.manager.loggerDict


def remove_logger(*loggers_or_names: Union[str, logging.Logger]) -> None:
    """
    Remove logger from logging module.

    :param loggers_or_names: Loggers or names of loggers to remove.
    :return: None
    """

    for logger_or_name in loggers_or_names:
        if isinstance(logger_or_name, logging.Logger):
            logger_name = logger_or_name.name
        elif isinstance(logger_or_name, str):
            logger_name = logger_or_name
        else:
            raise TypeError(f"Expected 'str' or 'logging.Logger', got '{type(logger_or_name)}'.")
        if not logger_exists(logger_name):
            continue
        logging.root.manager.loggerDict.pop(logger_name)
