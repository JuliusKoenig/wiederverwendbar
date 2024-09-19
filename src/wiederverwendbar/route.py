import logging
import sys
from ipaddress import IPv4Network, IPv4Address, AddressValueError

from wiederverwendbar.functions.run_command import run_command
from wiederverwendbar.pydantic.indexable_model import IndexableModel
from wiederverwendbar.functions.admin import is_admin

logger = logging.getLogger(__name__)


class Route(IndexableModel):
    target: IPv4Network
    gateway: IPv4Address


def _win_list_routes() -> list[Route]:
    """
    List all IPv4 routes on Windows.

    :return: List of Route objects
    """

    logger.debug("List all IPv4 routes on Windows.")

    # run route print -4
    success, stdout, stderr = run_command(cmd=["route", "print", "-4"])

    if not success:
        raise SystemExit(1)

    # find route section in stdout
    raw_routes = []
    separator_line_count = 0
    skip_next_lines = 0
    caption_skipped = False
    for line in stdout:
        if skip_next_lines > 0:
            skip_next_lines -= 1
            continue
        if line.startswith("==="):
            separator_line_count += 1
            continue
        if separator_line_count == 3:
            if not caption_skipped:
                skip_next_lines = 1
                caption_skipped = True
                continue
            raw_routes.append(line)

    # parse routes
    routes: list[Route] = []
    for raw_route in raw_routes:
        route_list = raw_route.split()
        # parse cidr
        mask_str = route_list[1]
        mask_list = [int(x) for x in mask_str.split(".")]
        cidr = sum((bin(x).count('1') for x in mask_list))

        # parse target
        target_str = route_list[0] + "/" + str(cidr)
        target = IPv4Network(target_str)

        # parse gateway
        try:
            gateway = IPv4Address(route_list[2])
        except AddressValueError:
            # take interface address as gateway
            gateway = IPv4Address(route_list[-2])

        route = Route(target=target, gateway=gateway)
        routes.append(route)

    logger.debug(f"Found {len(routes)} routes.")
    return routes


def list_routes() -> list[Route]:
    if sys.platform == "win32":
        return _win_list_routes()
    else:
        raise NotImplementedError("This function is not implemented for this platform.")


def _win_create_route(route: Route) -> bool:
    """
    Create a route on Windows.

    :param route: Route object
    :return: True if route was created successfully, False otherwise
    """

    logger.debug(f"Create route: {route}")

    # list existing routes
    existing_routes = _win_list_routes()

    # check if route already exists
    found_existing_route = None
    for existing_route in existing_routes:
        if existing_route.target == route.target:
            found_existing_route = existing_route
            break

    if found_existing_route is not None:
        logger.warning(f"Route {route} already exists. Found existing route: {found_existing_route}")

        return False

    # parse cmd
    cmd = ["route", "add", str(route.target), "mask", str(route.target.netmask), str(route.gateway)]

    success, stdout, stderr = run_command(cmd=cmd)

    # check if 'OK!' is in stdout
    if "OK!" not in stdout:
        success = False

    if not success:
        logger.error(f"Failed to create route {route}.")
        return False

    logger.info(f"Route {route} created.")
    return True


def create_route(route: Route) -> bool:
    """
    Create a route.

    :param route: Route object
    :return: True if route was created successfully, False otherwise
    """

    if not is_admin():
        logger.error("This function requires admin privileges.")
        raise SystemExit(1)

    if sys.platform == "win32":
        return _win_create_route(route=route)
    else:
        raise NotImplementedError("This function is not implemented for this platform.")


def _win_delete_route(route: Route) -> bool:
    """
    Create a route on Windows.

    :param route: Route object
    :return: True if route was created successfully, False otherwise
    """

    logger.debug(f"Create route: {route}")

    # list existing routes
    existing_routes = _win_list_routes()

    # check if route not exists
    found_existing_route = None
    for existing_route in existing_routes:
        if existing_route.target == route.target:
            found_existing_route = existing_route
            break

    if found_existing_route is None:
        logger.warning(f"Route {route} does not exist.")
        return False

    # parse cmd
    cmd = ["route", "delete", str(route.target), str(route.gateway)]

    success, stdout, stderr = run_command(cmd=cmd)

    # check if 'OK!' is in stdout
    if "OK!" not in stdout:
        success = False

    if not success:
        logger.error(f"Failed to delete route {route}.")
        return False

    logger.info(f"Route {route} deleted.")

    return True


def delete_route(route: Route) -> bool:
    if not is_admin():
        logger.error("This function requires admin privileges.")
        raise SystemExit(1)

    if sys.platform == "win32":
        return _win_delete_route(route=route)
    else:
        raise NotImplementedError("This function is not implemented for this platform.")
