import logging
import sys
from ipaddress import IPv4Network, IPv4Address, AddressValueError
from typing import Literal

from wiederverwendbar.functions.admin import require_admin
from wiederverwendbar.functions.run_command import run_command
from wiederverwendbar.pydantic import IndexableModel

logger = logging.getLogger(__name__)


class Route(IndexableModel):
    target: IPv4Network
    gateway: IPv4Address


@require_admin
class RouteManager:
    def __init__(self):
        if sys.platform == "win32":
            self._mode: Literal["windows", "linux"] = "windows"
        elif sys.platform == "linux":
            self._mode: Literal["windows", "linux"] = "linux"
        else:
            raise NotImplementedError(f"{RouteManager.__name__} is not implemented for this platform.")

    def __str__(self):
        return f"{self.__class__.__name__}(mode={self._mode})"

    @property
    def mode(self) -> Literal["windows", "linux"]:
        return self._mode

    @classmethod
    def _windows_get_all(cls) -> list[Route]:
        """
        List all IPv4 routes on Windows.

        :return: List of Route objects
        """

        # parse cmd
        cmd = ["route", "print", "-4"]
        success, stdout, stderr = run_command(cmd=cmd)
        if not success:
            raise RuntimeError(f"Failed to run command: {' '.join(cmd)}\n"
                               f"stdout: {stdout}\n"
                               f"stderr: {stderr}")

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
        return routes

    @classmethod
    def _linux_get_all(cls) -> list[Route]:
        """
        List all IPv4 routes on Linux.

        :return: List of Route objects
        """

        # parse cmd
        cmd = ["ip", "-4", "route", "list"]
        success, stdout, stderr = run_command(cmd=cmd)
        if not success:
            raise RuntimeError(f"Failed to run command: {' '.join(cmd)}\n"
                               f"stdout: {stdout}\n"
                               f"stderr: {stderr}")

        # parse routes
        routes: list[Route] = []
        for raw_route in stdout:
            route_list = raw_route.split()

            # parse target
            if route_list[0] == "default":
                target_str = "0.0.0.0/0"
            else:
                target_str = route_list[0]
            target = IPv4Network(target_str)

            # parse gateway
            try:
                gateway = IPv4Address(route_list[2])
            except AddressValueError:
                # find src
                src_index = 3
                while src_index < len(route_list):
                    if route_list[src_index] == "src":
                        break
                    src_index += 1
                # take interface address as gateway
                gateway = IPv4Address(route_list[src_index + 1])

            route = Route(target=target, gateway=gateway)
            routes.append(route)
        return routes

    def get_all(self) -> list[Route]:
        """
        Get all IPv4 routes.

        :return: List of Route objects
        """

        logger.info("List all IPv4 routes on Windows.")

        if self._mode == "windows":
            routes = self._windows_get_all()
        elif self._mode == "linux":
            routes = self._linux_get_all()
        else:
            raise NotImplementedError(f"{RouteManager.__name__}.{self.get_all.__name__}() is not implemented for this platform.")

        logger.debug(f"Found {len(routes)} routes.")

        return routes

    @classmethod
    def _windows_create(cls, route: Route) -> bool:
        """
        Create a route on Windows.

        :param route: Route object
        :return: True if route was created successfully, False otherwise
        """

        # parse cmd
        cmd = ["route", "add", str(route.target), "mask", str(route.target.netmask), str(route.gateway)]
        success, stdout, stderr = run_command(cmd=cmd)
        if not success:
            raise RuntimeError(f"Failed to run command: {' '.join(cmd)}\n"
                               f"stdout: {stdout}\n"
                               f"stderr: {stderr}")

        # check if 'OK!' is in stdout
        if "OK!" not in stdout:
            success = False
        if not success:
            return False
        return True

    @classmethod
    def _linux_create(cls, route: Route) -> bool:
        """
        Create a route on Linux.

        :param route: Route object
        :return: True if route was created successfully, False otherwise
        """

        # parse cmd
        cmd = ["ip", "route", "add", str(route.target), "via", str(route.gateway)]
        success, stdout, stderr = run_command(cmd=cmd)
        if not success:
            raise RuntimeError(f"Failed to run command: {' '.join(cmd)}\n"
                               f"stdout: {stdout}\n"
                               f"stderr: {stderr}")
        if not success:
            return False
        return True

    def create(self, *routes: Route) -> list[bool]:
        """
        Create a route.

        :param routes: Route objects
        :return: A list of boolean for each Route, True if route was created successfully, False otherwise
        """

        results = []
        if len(routes) == 0:
            return results

        # list existing routes
        existing_routes = self.get_all()

        for route in routes:
            # check if route already exists
            found_existing_route = None
            for existing_route in existing_routes:
                if existing_route.target == route.target:
                    found_existing_route = existing_route
                    break
            if found_existing_route is not None:
                logger.warning(f"Route {route} already exists. Found existing route: {found_existing_route}")
                results.append(False)
                continue

            logger.info(f"Create route: {route}")
            if self._mode == "windows":
                result = self._windows_create(route=route)
            elif self._mode == "linux":
                result = self._linux_create(route=route)
            else:
                raise NotImplementedError(f"{RouteManager.__name__}.{self.create.__name__}() is not implemented for this platform.")
            if result:
                logger.debug(f"Route {route} created.")
            else:
                logger.error(f"Failed to create route {route}.")
            results.append(result)
        return results

    @classmethod
    def _windows_delete(cls, route: Route) -> bool:
        """
        Delete a route on Windows.

        :param route: Route object
        :return: True if route was deleted successfully, False otherwise
        """

        # parse cmd
        cmd = ["route", "delete", str(route.target), str(route.gateway)]
        success, stdout, stderr = run_command(cmd=cmd)
        if not success:
            raise RuntimeError(f"Failed to run command: {' '.join(cmd)}\n"
                               f"stdout: {stdout}\n"
                               f"stderr: {stderr}")

        # check if 'OK!' is in stdout
        if "OK!" not in stdout:
            success = False
        if not success:
            return False
        return True

    @classmethod
    def _linux_delete(cls, route: Route) -> bool:
        """
        Delete a route on Linux.

        :param route: Route object
        :return: True if route was deleted successfully, False otherwise
        """

        # parse cmd
        cmd = ["ip", "route", "del", str(route.target), "via", str(route.gateway)]
        success, stdout, stderr = run_command(cmd=cmd)
        if not success:
            raise RuntimeError(f"Failed to run command: {' '.join(cmd)}\n"
                               f"stdout: {stdout}\n"
                               f"stderr: {stderr}")
        if not success:
            return False
        return True

    def delete(self, *routes: Route) -> list[bool]:
        """
        Delete a route.

        :param routes: Route objects
        :return: A list of boolean for each Route, True if route was deleted successfully, False otherwise
        """

        results = []
        if len(routes) == 0:
            return results

        # list existing routes
        existing_routes = self.get_all()

        for route in routes:
            # check if route not exists
            found_existing_route = None
            for existing_route in existing_routes:
                if existing_route.target == route.target:
                    found_existing_route = existing_route
                    break
            if found_existing_route is None:
                logger.warning(f"Route {route} does not exist.")
                results.append(False)
                continue

            logger.info(f"Delete route: {route}")
            if self._mode == "windows":
                result = self._windows_delete(route=route)
            elif self._mode == "linux":
                result = self._linux_delete(route=route)
            else:
                raise NotImplementedError(f"{RouteManager.__name__}.{self.delete.__name__}() is not implemented for this platform.")
            if result:
                logger.debug(f"Route {route} deleted.")
            else:
                logger.error(f"Failed to delete route {route}.")
            results.append(result)
        return results
