import json
import logging
import asyncio
import warnings
from typing import Optional, Any

import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route, WebSocketRoute
from starlette.requests import Request
from starlette.endpoints import WebSocketEndpoint
from starlette.websockets import WebSocket
from starlette_admin.base import BaseAdmin
from starlette_admin.contrib.mongoengine import Admin, ModelView
from starlette_admin.actions import action
from mongoengine import connect, Document, StringField

logger = logging.getLogger(__name__)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)

# connect to database
connect("test",
        host="localhost",
        port=27017)

# Create starlette app
app = Starlette(
    routes=[
        Route(
            "/",
            lambda r: HTMLResponse("<a href=/admin/>Click me to get to Admin!</a>"),
        ),
    ],
)


class ActionLogger(logging.Logger):
    class WebsocketHandler(logging.Handler):
        def __init__(self, websocket: WebSocket):
            super().__init__()
            self.websocket = websocket

        def emit(self, record: logging.LogRecord) -> None:
            # check if record is command
            if getattr(record, "command", False):
                command = json.loads(record.msg)
            else:
                msg = self.format(record)
                command = {"command": "log", "value": msg}
            command_json = json.dumps(command)

            # send command message
            try:
                asyncio.run(self.websocket.send_text(command_json))
            except Exception:
                self.handleError(record)

    def __init__(self, action_log_key: str, websocket: Optional[WebSocket] = None):
        super().__init__(name=self._name(action_log_key))

        self.action_log_key = action_log_key

        # check if logger already exists
        if ActionLogger.is_logger_exist(action_log_key=action_log_key):
            raise ValueError("Logger already exists.")

        # create websocket handler
        if websocket is not None:
            websocket_handler = self.WebsocketHandler(websocket=websocket)
            self.addHandler(websocket_handler)

        # add logger to logger manager
        logging.root.manager.loggerDict[self._name(action_log_key=action_log_key)] = self

        self._started = False
        self._use_steps = False
        self._steps = 1
        self._step = 0

    def __del__(self):
        self.exit()

    @classmethod
    def _name(cls, action_log_key: str) -> str:
        return f"{cls.__name__} - {action_log_key}"

    @classmethod
    def get_logger(cls, action_log_key: str) -> Optional["ActionLogger"]:
        # get all logger
        all_loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]

        # check if logger already exists
        for _logger in all_loggers:
            if action_log_key != getattr(_logger, "action_log_key", None):
                continue
            if not isinstance(_logger, ActionLogger):
                continue
            return _logger
        return None

    @classmethod
    def get_logger_by_request(cls, request: Request) -> Optional["ActionLogger"]:
        action_log_key = request.query_params.get("actionLogKey", None)
        if action_log_key is None:
            raise ValueError("No action log key provided.")
        return cls.get_logger(action_log_key=action_log_key)

    @classmethod
    def is_logger_exist(cls, action_log_key: str) -> bool:
        return cls.get_logger(action_log_key=action_log_key) is not None

    def _log(
            self,
            level,
            msg,
            args,
            exc_info=None,
            extra=None,
            stack_info=False,
            stacklevel=1,
    ):
        if not self.is_started:
            raise ValueError("Logger not started.")
        super()._log(level, msg, args, exc_info, extra, stack_info, stacklevel)

    def _command(self, command: str, value: Any):

        command_json = json.dumps({"command": command, "value": value})

        record = self.makeRecord(self.name, logging.NOTSET, "command", 0, command_json, (), None, extra={"command": True})
        self.handle(record)

    def _step_command(self):
        if not self.is_steps_used:
            return
        calculated_progress = round(self.step / self.steps * 100)

        self._command("step", calculated_progress)

    @property
    def is_started(self) -> bool:
        return self._started

    @property
    def is_steps_used(self) -> bool:
        return self._use_steps

    @property
    def steps(self) -> int:
        return self._steps

    @steps.setter
    def steps(self, value: int):
        if value < 0:
            raise ValueError("Steps must be greater than 0.")
        self._steps = value
        self._step_command()

    @property
    def step(self) -> int:
        return self._step

    @step.setter
    def step(self, value: int):
        self._step = value
        self._step_command()

    def start(self):
        self._command("start", None)
        # send use steps command
        if self._use_steps:
            self._command("use_steps", None)
        self._started = True

    def use_steps(self) -> None:
        self._use_steps = True
        self._command("use_steps", None)

    def next_step(self):
        if self.step >= self.steps:
            return
        self.step += 1

    def finalize(self):
        self.step = self.steps
        self._command("finalize", None)
        self._started = False

    def exit(self):
        # if self.is_started:
        #     self.finalize()
        #     return

        # remove handler
        for handler in self.handlers:
            self.removeHandler(handler)

        # remove logger from logger manager
        logging.root.manager.loggerDict.pop(self.name, None)


class ActionLog:
    def __init__(self,
                 request: Request,
                 log_level: Optional[int] = None,
                 parent: Optional[logging.Logger] = logger,
                 formatter: logging.Formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d - %H:%M:%S"),
                 timeout: int = 5,
                 ignore_not_found: bool = False,
                 steps: Optional[int] = None):
        """
        Action log context manager.

        :param request: Request object.
        :param log_level: Log level. Default is parent log level. If parent not provided, default is INFO.
        :param parent: Parent logger. Default is the module logger.
        :param formatter: Log formatter. Default is "%(asctime)s - %(levelname)s - %(message)s" with date format "%Y-%m-%d - %H:%M:%S".
        :param timeout: Timeout in seconds to wait for action logger. Default is 5 seconds.
        :param steps: Number of steps. Default is None.
        """
        self.request = request

        # get action logger
        current_try = 0
        while current_try < timeout:
            self.action_logger = ActionLogger.get_logger_by_request(request)
            if self.action_logger is not None:
                break
            current_try += 1
            logger.debug(f"[{current_try}/{timeout}] Waiting for action logger...")
            asyncio.run(asyncio.sleep(1))
        if self.action_logger is None:
            if not ignore_not_found:
                raise ValueError("Action logger not found.")
            # create dummy logger and warn
            self.action_logger = ActionLogger(action_log_key=request.query_params.get("actionLogKey", "dummy"))
            warnings.warn("Action logger not found. Created dummy logger.", RuntimeWarning)

        # set log level
        if log_level is None:
            if parent is None:
                log_level = logging.INFO
            else:
                log_level = parent.level
        self.action_logger.setLevel(log_level)

        # set parent logger
        self.action_logger.parent = parent

        # set formatter
        for handler in self.action_logger.handlers:
            handler.setFormatter(formatter)

        self._steps = steps

    def __enter__(self) -> ActionLogger:
        self.action_logger.start()
        if self._steps is not None:
            self.action_logger.use_steps()
            self.action_logger.steps = self._steps
        return self.action_logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        ...
        # self.action_logger.finalize()


class ActionLogEndpoint(WebSocketEndpoint):
    encoding = "text"

    @property
    def action_log_key(self) -> str:
        if "path_params" not in self.scope:
            raise ValueError("No path params in scope.")
        if "action_log_key" not in self.scope["path_params"]:
            raise ValueError("No action log key in path params.")
        return self.scope["path_params"]["action_log_key"]

    async def on_connect(self, websocket: WebSocket):
        try:
            # create logger
            ActionLogger(action_log_key=self.action_log_key, websocket=websocket)
        except Exception as e:
            await websocket.close(code=1000)
            raise

        await websocket.accept()

    async def on_disconnect(self, websocket: WebSocket, close_code: int):
        # get logger
        action_logger = ActionLogger.get_logger(self.action_log_key)
        if action_logger is None:
            return

        # exit logger
        action_logger.exit()


class CustomActionAdmin(BaseAdmin):
    def init_routes(self) -> None:
        super().init_routes()
        self.routes.append(WebSocketRoute(path="/ws/action_log/{action_log_key}", endpoint=ActionLogEndpoint, name="action_log"))  # noqa


class MyAdmin(Admin, CustomActionAdmin):
    ...


# Create admin
admin = MyAdmin(title="Test Admin",
                statics_dir="statics")


class Test(Document):
    meta = {"collection": "test"}

    test_str = StringField()


class TestView(ModelView):
    def __init__(self):
        super().__init__(document=Test, icon="fa fa-server", name="Test", label="Test")

    actions = ["delete", "test_action_normal", "test_action_action_log"]

    @action(name="test_action_normal",
            text="Test Action - Normal",
            confirmation="Möchtest du die Test Aktion durchführen?",
            icon_class="fa-regular fa-network-wired",
            submit_btn_text="Ja, fortsetzen",
            submit_btn_class="btn-success")
    async def test_action_normal(self, request: Request, pk: list[str]) -> str:
        await asyncio.sleep(2)

        return "Test Aktion erfolgreich."

    @action(name="test_action_action_log",
            text="Test Action - Action Log",
            confirmation="Möchtest du die Test Aktion durchführen?",
            icon_class="fa-regular fa-network-wired",
            submit_btn_text="Ja, fortsetzen",
            submit_btn_class="btn-success")
    async def test_action_action_log(self, request: Request, pk: list[str]) -> str:
        with ActionLog(request, log_level=logging.DEBUG, steps=3) as action_logger:
            action_logger.debug("Debug")
            action_logger.info("Test Aktion step 1")
            action_logger.next_step()
            await asyncio.sleep(2)
            action_logger.info("Test Aktion step 2")
            action_logger.next_step()
            await asyncio.sleep(2)
            # action_logger.steps += 100
            # for i in range(1, 100):
            #     action_logger.info(f"Test Aktion step 2 - {i}")
            #     action_logger.next_step()
            #     await asyncio.sleep(0.1)
            action_logger.info("Test Aktion step 3")
            action_logger.next_step()
            await asyncio.sleep(2)

        return "Test Aktion erfolgreich."


# Add views to admin#
admin.add_view(TestView())

# Mount admin to app
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

