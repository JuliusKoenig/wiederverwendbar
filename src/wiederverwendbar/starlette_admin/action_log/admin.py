import asyncio
import logging
from warnings import warn
from threading import Thread, Lock
from typing import Union, Any, Optional
from socket import timeout as socket_timeout

import nest_asyncio
from jinja2 import PackageLoader
from pydantic import ValidationError
from starlette.applications import Starlette
from starlette.routing import WebSocketRoute, Mount
from starlette.endpoints import WebSocketEndpoint
from starlette.websockets import WebSocket, WebSocketState
from starlette.types import Scope, Receive, Send
from kombu import Connection, Exchange, Queue, Producer

from wiederverwendbar.starlette_admin.admin import MultiPathAdmin
from wiederverwendbar.starlette_admin.action_log.logger import ActionLogger, ActionLoggerResponse

logger = logging.getLogger(__name__)


class ActionLogAdmin(MultiPathAdmin):
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
            with self.connection.Consumer([self.log_queue], callbacks=[self.send_log]) as consumer:
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
            self.exchange, self.start_queue, self.log_queue, self.response_queue, self.exit_queue = ActionLogger.get_action_log_queues(websocket)

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
                self.exit_queue = None
                self.producer = None
                self.websocket = None

    def __init__(
            self,
            *args,
            kombu_connection: Connection,
            **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.kombu_connection = kombu_connection

    def init_routes(self) -> None:
        super().init_routes()
        self.routes.append(WebSocketRoute(path="/ws/action_log/{action_log_key}", endpoint=self.ActionLogEndpoint, name="action_log"))  # noqa

        nest_asyncio.apply()  # ToDo: ugly hack to make asyncio.run work outside of debug mode, remove if it's not needed anymore

    def mount_to(self, app: Starlette) -> None:
        super().mount_to(app)

        # get admin app
        admin_app = None
        for app in app.routes:
            if not isinstance(app, Mount):
                continue
            if app.name != self.route_name:
                continue
            admin_app = app.app
        if admin_app is None:
            raise ValueError("Admin app not found")

        # add kombu connection to admin app
        admin_app.state.kombu_connection = self.kombu_connection
