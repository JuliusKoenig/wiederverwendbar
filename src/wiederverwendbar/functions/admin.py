import ctypes
import logging
import os
from functools import wraps
from typing import Optional

logger = logging.getLogger(__name__)


def is_admin() -> bool:
    """
    Check if the current user has admin privileges.

    :return: True if the user has admin privileges, False otherwise
    """

    logger.debug("Check if the current user has admin privileges.")

    try:
        _is_admin = os.getuid() == 0
    except AttributeError:
        _is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0

    logger.debug(f"Current user {'has' if _is_admin else 'does not have'} admin privileges.")

    return _is_admin


def require_admin(show_window: Optional[int] = None):
    def decorator(func):
        """
        Decorator to require admin rights
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            Wrapper function
            """

            # check if is admin
            if not is_admin():
                logger.error("This function requires admin rights.")
                raise SystemExit(1)

            return func(*args, **kwargs)

        return wrapper

    return decorator
