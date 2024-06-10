import logging
from ipaddress import IPv4Address
from typing import Union

from pythonping import ping

logger = logging.getLogger(__name__)


def wait_ping(host: Union[str, IPv4Address], timeout: int = 3, count: int = 5, verbose: bool = False) -> bool:
    """
    Wait until the remote host is pingable.

    :param host: Remote host
    :param timeout: Timeout in seconds.
    :param count: Number of pings. If -1, ping endlessly.
    :param verbose: Verbose output.
    :return: True if the remote host is pingable, False otherwise.
    """

    if type(host) is IPv4Address:
        host = str(host)

    logger.debug(f"Wait until '{host}' is pingable.")

    # ping remote host
    if count == -1:
        _count = 1
        while True:
            ping_result = ping(host, timeout=timeout, count=_count, verbose=verbose)
            if ping_result.success():
                break
    else:
        _count = count
        ping_result = ping(host, timeout=timeout, count=_count, verbose=verbose)

    if not ping_result.success():
        logger.error(f"Remote host '{host}' is not pingable.")
        return False

    logger.debug(f"Remote host '{host}' is pingable.")
    return True
