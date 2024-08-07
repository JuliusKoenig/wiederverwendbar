import logging

from jinja2 import PackageLoader
from starlette.routing import WebSocketRoute
from starlette.endpoints import WebSocketEndpoint
from starlette.websockets import WebSocket

from wiederverwendbar.starlette_admin.admin import MultiPathAdmin
from wiederverwendbar.starlette_admin.action_log.logger import ActionLogger

logger = logging.getLogger(__name__)


class ActionLogAdmin(MultiPathAdmin):
    static_files_packages = [("wiederverwendbar", "starlette_admin/action_log/statics")]
    template_packages = [PackageLoader("wiederverwendbar", "starlette_admin/action_log/templates")]

    class ActionLogEndpoint(WebSocketEndpoint):
        encoding = "text"
        wait_for_logger_timeout = 5

        async def on_connect(self, websocket: WebSocket):
            await websocket.accept()

            # wait for action logger
            try:
                action_logger = await ActionLogger.wait_for_logger(websocket, timeout=self.wait_for_logger_timeout)
            except ValueError:
                await websocket.close(code=1008)
                return

            # add websocket to action logger
            action_logger.add_websocket(websocket)

        async def on_disconnect(self, websocket: WebSocket, close_code: int):
            # get logger
            action_logger = await ActionLogger.get_logger(websocket)
            if action_logger is None:
                return

            # remove websocket from logger
            action_logger.remove_websocket(websocket)

    def init_routes(self) -> None:
        super().init_routes()
        self.routes.append(WebSocketRoute(path="/ws/action_log/{action_log_key}", endpoint=self.ActionLogEndpoint, name="action_log"))  # noqa
