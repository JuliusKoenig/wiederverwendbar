import logging
from typing import Optional, Union, Any, Callable, Awaitable

from fastapi import FastAPI, Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Route, Mount

from wiederverwendbar.default import Default
from wiederverwendbar.fastapi.root.settings import RootAppSettings

logger = logging.getLogger(__name__)


class RootApp(FastAPI):
    def __init__(self,
                 debug: Union[Default, bool] = Default(),
                 root_path: Union[Default, str] = Default(),
                 root_path_in_servers: Union[Default, bool] = Default(),
                 root_redirect: Union[Default, None, str] = Default(),
                 settings: Optional[RootAppSettings] = None,
                 **kwargs):

        # set default
        if settings is None:
            settings = RootAppSettings()

        if type(debug) is Default:
            debug = settings.debug
        if type(debug) is Default:
            debug = False

        if type(root_path) is Default:
            root_path = settings.root_path
        if type(root_path) is Default:
            root_path = ""

        if root_path_in_servers is None:
            root_path_in_servers = settings.root_path_in_servers
        if type(root_path_in_servers) is Default:
            root_path_in_servers = True

        # set attrs
        self.root_redirect = root_redirect

        # For storing the original "add_api_route" method from router.
        # If None, the access to router will be blocked.
        self._original_add_route: Union[None, bool, Callable, Any] = None
        self._original_add_api_route: Union[None, bool, Callable, Any] = None
        self._original_add_api_websocket_route: Union[None, bool, Callable, Any] = None

        super().__init__(debug=debug,
                         root_path=root_path,
                         root_path_in_servers=root_path_in_servers,
                         **kwargs)

        logger.info(f"Initialized FastAPI: {self}")

    def __str__(self):
        return f"{self.__class__.__name__}(title={self.title}, version={self.version})"

    def __getattribute__(self, item):
        # block router access if the init flag is not set
        if item == "router":
            if self._original_add_route is None or self._original_add_api_route is None or self._original_add_api_websocket_route is None:
                raise RuntimeError("Class is not initialized!")
        return super().__getattribute__(item)

    def _add_route(self,
                   path: str,
                   endpoint: Callable[[Request], Union[Awaitable[Response], Response]],
                   methods: Optional[list[str]] = None,
                   name: Optional[str] = None,
                   include_in_schema: bool = True, *args, **kwargs) -> None:
        if self._original_add_route is None or self._original_add_route is True:
            raise RuntimeError("Original add_route method is not set!")
        logger.debug(f"Adding route for {self} -> {path}")
        return self._original_add_route(path, endpoint, methods, name, include_in_schema, *args, **kwargs)

    def _add_api_route(self,
                       path: str,
                       endpoint: Callable[..., Any],
                       *args,
                       **kwargs) -> None:
        if self._original_add_api_route is None or self._original_add_api_route is True:
            raise RuntimeError("Original add_api_route method is not set!")
        logger.debug(f"Adding API route for {self} -> {path}")
        return self._original_add_api_route(path, endpoint, *args, **kwargs)

    def _add_api_websocket_route(self,
                                 path: str,
                                 endpoint: Callable[..., Any],
                                 name: Optional[str] = None,
                                 *args,
                                 **kwargs) -> None:
        if self._original_add_api_websocket_route is None or self._original_add_api_websocket_route is True:
            raise RuntimeError("Original add_api_websocket_route method is not set!")
        logger.debug(f"Adding API websocket route for {self} -> {path}")
        return self._original_add_api_websocket_route(path, endpoint, name, *args, **kwargs)

    def setup(self) -> None:
        # to unblock router access
        self._original_add_route = True
        self._original_add_api_route = True
        self._original_add_api_websocket_route = True

        # overwrite add_api_route for router
        # noinspection PyTypeChecker
        self._original_add_api_route = self.router.add_api_route
        self.router.add_api_route = self._add_api_route
        # noinspection PyTypeChecker
        self._original_add_api_websocket_route = self.router.add_api_websocket_route
        self.router.add_api_websocket_route = self._add_api_websocket_route
        # noinspection PyTypeChecker
        self._original_add_route = self.router.add_route
        self.router.add_route = self._add_route

        # create root redirect route
        async def get_root_redirect(request: Request) -> RedirectResponse:
            url, status_code = await self.get_root_redirect(request=request)
            return RedirectResponse(url=url, status_code=status_code)

        if self.root_redirect:
            self.add_route(path="/", route=get_root_redirect, include_in_schema=False)

    async def get_root_redirect(self, request: Request) -> tuple[str, int]:
        if self.root_redirect is None:
            raise RuntimeError("Root Redirect not set")
        for route in self.routes:
            if not isinstance(route, Route) and not isinstance(route, Mount):
                continue
            if route.path == "/" and route.name == "get_root_redirect":
                continue
            return request.scope.get("root_path", "").rstrip("/") + route.path, 307
        raise RuntimeError("Cannot find any route to redirect to")
