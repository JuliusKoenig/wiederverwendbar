import asyncio
import logging
from pathlib import Path
from warnings import warn
from threading import Thread, Lock
from typing import Union, Any
from socket import timeout as socket_timeout

import nest_asyncio
from jinja2 import PackageLoader
from pydantic import ValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import FileResponse
from starlette.routing import WebSocketRoute, Route
from starlette.endpoints import WebSocketEndpoint
from starlette.websockets import WebSocket, WebSocketState
from starlette.types import Scope, Receive, Send
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette_admin.i18n import I18nConfig
from starlette_admin.views import CustomView
from starlette_admin.auth import BaseAuthProvider
from kombu import Connection, Exchange, Queue, Producer

from typing import Optional, Sequence

from wiederverwendbar.starlette_admin.action_log.settings import ActionLogAdminSettings
from wiederverwendbar.starlette_admin.settings.admin import SettingsAdminMeta, SettingsAdmin
from wiederverwendbar.starlette_admin.multi_path.admin import MultiPathAdminMeta, MultiPathAdmin
from wiederverwendbar.starlette_admin.action_log.logger import ActionLogger, ActionLoggerResponse

logger = logging.getLogger(__name__)


class ActionLogAdminMeta(SettingsAdminMeta, MultiPathAdminMeta):
    ...


class ActionLogAdmin(SettingsAdmin, MultiPathAdmin, metaclass=ActionLogAdminMeta):
    settings_class = ActionLogAdminSettings
    static_files_packages = [("wiederverwendbar", "starlette_admin/action_log/statics")]
    template_packages = [PackageLoader("wiederverwendbar", "starlette_admin/action_log/templates")]

    class ActionLogEndpoint(WebSocketEndpoint):
        encoding = "text"
        wait_for_logger_timeout = 5

        def __init__(self, scope: Scope, receive: Receive, send: Send):
            super().__init__(scope=scope, receive=receive, send=send)

            self.loop = asyncio.get_event_loop()
            self.websocket: Optional[WebSocket] = None
            self.connection: Optional[Connection] = None
            self.exchange: Optional[Exchange] = None
            self.start_queue: Optional[Queue] = None
            self.log_queue: Optional[Queue] = None
            self.response_queue: Optional[Queue] = None
            self.download_queue: Optional[Queue] = None
            self.exit_queue: Optional[Queue] = None
            self.producer: Optional[Producer] = None
            self.log_thread = Thread(target=self.receive_logs)
            self.lock = Lock()

        @property
        def ready(self):
            with self.lock:
                if self.connection is None:
                    return False
                if self.exchange is None:
                    return False
                if self.start_queue is None:
                    return False
                if self.log_queue is None:
                    return False
                if self.response_queue is None:
                    return False
                if self.download_queue is None:
                    return False
                if self.exit_queue is None:
                    return False
                if self.producer is None:
                    return False
                if self.websocket is None:
                    return False
                if self.websocket.client_state != WebSocketState.CONNECTED:
                    return False
                return True

        def receive_logs(self):
            with self.connection.Consumer([self.log_queue], callbacks=[self.send_log]):
                while True:
                    if not self.ready:
                        break
                    try:
                        self.connection.drain_events(timeout=0.001)
                    except socket_timeout:
                        ...

        def send_log(self, body, message):
            if not self.ready:
                warn(f"Cannot send log to websocket, because it is not connected -> {body}", UserWarning)
            with self.lock:
                asyncio.run_coroutine_threadsafe(self.websocket.send_json(body), self.loop)
            message.ack()

        def response(self, data: Union[str, dict[str, Any], ActionLoggerResponse]) -> bool:
            if not isinstance(data, ActionLoggerResponse):
                try:
                    data = ActionLogger.parse_response_obj(data)
                except ValidationError:
                    return False
            data_dict = data.model_dump()

            self.producer.publish(data_dict, exchange=self.exchange, routing_key=self.response_queue.name)

            return True

        async def on_connect(self, websocket: WebSocket):
            if self.websocket is not None:
                await websocket.close(code=1008)
                return

            # get kombu connection
            self.connection = ActionLogger.get_kombu_connection(request_or_websocket=websocket)

            # create exchange and queues from websocket request
            self.exchange, self.start_queue, self.log_queue, self.response_queue, self.download_queue, self.exit_queue = ActionLogger.get_action_log_queues(
                request_or_websocket=websocket)

            # create producer
            self.producer = self.connection.Producer(serializer='json')

            # accept websocket
            await websocket.accept()

            # save websocket
            self.websocket = websocket

            # start log thread
            self.log_thread.start()

            # send start message to logger
            self.producer.publish({"start": "start"}, exchange=self.exchange, routing_key=self.start_queue.name)

        async def on_receive(self, websocket: WebSocket, data: str):
            # send response to logger
            if not self.response(data=data):
                # close websocket
                await websocket.close(code=1008)

        async def on_disconnect(self, websocket: WebSocket, close_code: int):
            self.producer.publish({"exit": "exit"}, exchange=self.exchange, routing_key=self.exit_queue.name)

            with self.lock:
                self.connection = None
                self.exchange = None
                self.start_queue = None
                self.log_queue = None
                self.response_queue = None
                self.download_queue = None
                self.exit_queue = None
                self.producer = None
                self.websocket = None

    def __init__(
            self,
            kombu_connection: Connection,
            title: Optional[str] = None,
            base_url: Optional[str] = None,
            route_name: Optional[str] = None,
            logo_url: Optional[str] = None,
            login_logo_url: Optional[str] = None,
            templates_dir: Optional[str] = None,
            statics_dir: Optional[str] = None,
            index_view: Optional[CustomView] = None,
            auth_provider: Optional[BaseAuthProvider] = None,
            middlewares: Optional[Sequence[Middleware]] = None,
            session_middleware: Optional[type[SessionMiddleware]] = None,
            debug: Optional[bool] = None,
            i18n_config: Optional[I18nConfig] = None,
            favicon_url: Optional[str] = None,
            settings: Optional[ActionLogAdminSettings] = None
    ):
        super().__init__(
            title=title,
            base_url=base_url,
            route_name=route_name,
            logo_url=logo_url,
            login_logo_url=login_logo_url,
            templates_dir=templates_dir,
            statics_dir=statics_dir,
            index_view=index_view,
            auth_provider=auth_provider,
            middlewares=middlewares,
            session_middleware=session_middleware,
            debug=debug,
            i18n_config=i18n_config,
            favicon_url=favicon_url,
            settings=settings
        )

        self.kombu_connection = kombu_connection

    def init_routes(self) -> None:
        super().init_routes()
        self.routes.append(WebSocketRoute(path="/ws/action_log/{action_log_key}", endpoint=self.ActionLogEndpoint, name="action_log"))  # noqa
        self.routes.append(Route("/action_log/download/{action_log_key}", self.action_log_download, methods=["GET"], name="action_log_download"))  # noqa

        nest_asyncio.apply()  # ToDo: ugly hack to make asyncio.run work outside of debug mode, remove if it's not needed anymore

    def action_log_download(self, request: Request):
        # get action_log_key from request
        action_log_key = request.path_params.get("action_log_key", None)
        if action_log_key is None:
            raise HTTPException(status_code=404, detail="Action Log Key not provided.")

        # get download queue
        exchange, start_queue, log_queue, response_queue, download_queue, exit_queue = ActionLogger.get_action_log_queues(request_or_websocket=request)

        download_file: Optional[Path] = None

        def send_file(body, message):
            nonlocal download_file

            download_file = Path(body["file_path"])
            # message.ack()

        # get download file from download queue
        with self.kombu_connection.Consumer([download_queue], callbacks=[send_file]):
            try:
                self.kombu_connection.drain_events(timeout=5)
            except socket_timeout:
                raise HTTPException(status_code=500, detail="Timeout while waiting for download file.")

        if download_file is None:
            raise HTTPException(status_code=500, detail="No download file received.")
        elif not download_file.is_file():
            raise HTTPException(status_code=404, detail="Download file not found.")

        return FileResponse(download_file, filename=download_file.name)
