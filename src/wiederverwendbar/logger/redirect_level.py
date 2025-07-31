import logging
from typing import Optional, Union


def redirect_level(logger: Union[str, logging.Logger],
                   to: int,
                   *,
                   lt: Optional[int] = None,
                   lte: Optional[int] = None,
                   eq: Optional[int] = None,
                   gte: Optional[int] = None,
                   gt: Optional[int] = None) -> None:
    """
    Redirects the log level of a logger to a specified level based on conditions.

    :param logger: The logger or logger name to redirect the level for.
    :param to: The log level to redirect to.
    :param lt: If the current level is less than this value, redirect to `to`.
    :param lte: If the current level is less than or equal to this value, redirect to `to`.
    :param eq: If the current level is equal to this value, redirect to `to`.
    :param gte: If the current level is greater than or equal to this value, redirect to `to`.
    :param gt: If the current level is greater than this value, redirect to `to`.
    :return: None
    """

    if isinstance(logger, str):
        logger = logging.getLogger(logger)
    if not isinstance(logger, logging.Logger):
        raise TypeError(f"Expected a logger or a logger name, got {type(logger)}")
    _all = False
    if lt is None and lte is None and eq is None and gte is None and gt is None:
        _all = True

    original__log = logger._log

    def _log(level, *args, **kwargs):
        if _all:
            level = to
        elif lt is not None and level < lt:
            level = to
        elif lte is not None and level <= lte:
            level = to
        elif eq is not None and level == eq:
            level = to
        elif gte is not None and level >= gte:
            level = to
        elif gt is not None and level > gt:
            level = to
        if logger.isEnabledFor(level):
            original__log(level, *args, **kwargs)

    logger._log = _log
