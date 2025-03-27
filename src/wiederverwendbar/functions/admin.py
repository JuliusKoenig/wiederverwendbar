import ctypes
import logging
import os
from functools import wraps
from types import FunctionType

logger = logging.getLogger(__name__)


class NoAdminPrivilegesError(RuntimeError):
    ...


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


def require_admin(func_or_object):
    """
    Decorator to require admin rights
    """

    @wraps(func_or_object)
    def wrapper(*args, **kwargs):
        """
        Wrapper function
        """

        # check if callable
        if not callable(func_or_object):
            raise TypeError(f"{func_or_object.__name__} is not callable.")

        # check if is admin
        if not is_admin():
            type_str = "Function" if isinstance(func_or_object, FunctionType) else "Object"
            error_msg = f"{type_str} '{func_or_object.__name__}' requires admin rights."
            logger.error(error_msg)
            raise NoAdminPrivilegesError(error_msg)

        return func_or_object(*args, **kwargs)

    return wrapper
