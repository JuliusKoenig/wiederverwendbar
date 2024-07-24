import json
import logging
import asyncio
import string
import warnings
from typing import Optional, Union

import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route, WebSocketRoute
from starlette.requests import Request
from starlette.endpoints import WebSocketEndpoint
from starlette.websockets import WebSocket, WebSocketState
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


class WebsocketHandler(logging.Handler):
    def __init__(self, websocket: WebSocket):
        super().__init__()
        self.websocket = websocket

    def emit(self, record: logging.LogRecord) -> None:
        # get extra
        sub_logger_name = getattr(record, "sub_logger")
        command = getattr(record, "command", None)

        command_dict = {"sub_logger": sub_logger_name}

        # check if record is command
        if command is not None:
            command_dict.update(command)
        else:
            msg = self.format(record)
            command_dict.update({"command": "log", "value": msg})

        # convert command to json
        command_json = json.dumps(command_dict)

        # send command message
        try:
            asyncio.run(self.websocket.send_text(command_json))
        except Exception:
            self.handleError(record)


class ActionSubLogger(logging.Logger):
    def __init__(self, action_logger: "ActionLogger", name: str, title: Optional[str] = None):
        super().__init__(name=action_logger.action_log_key + "." + name)

        # validate name
        if not name:
            raise ValueError("Name must not be empty.")
        for char in name:
            if char not in string.ascii_letters + string.digits + "-" + "_":
                raise ValueError("Invalid character in name. Only a-z, A-Z, 0-9, - and _ are allowed.")

        if title is None:
            title = name
        self._title = title
        self._action_logger = action_logger
        self._steps: Optional[int] = None
        self._step: int = 0

        # check if logger already exists
        if self.is_logger_exist(name=self.name):
            raise ValueError("ActionSubLogger already exists.")

        # create websocket handler
        if self._action_logger.websocket is not None:
            websocket_handler = WebsocketHandler(websocket=self._action_logger.websocket)
            self.addHandler(websocket_handler)

        # add logger to logger manager
        logging.root.manager.loggerDict[self.name] = self

        # start sub logger
        self._command("start", self.title)

    def __del__(self):
        if not self.exited:
            self.exit()

    @classmethod
    def _get_logger(cls, name: str) -> Optional["ActionSubLogger"]:
        # get all logger
        all_loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]

        # filter action logger
        for _logger in all_loggers:
            if name != _logger.name:
                continue
            if not isinstance(_logger, ActionSubLogger):
                continue
            return _logger
        return None

    @classmethod
    def is_logger_exist(cls, name: str) -> bool:
        return cls._get_logger(name=name) is not None

    def _extra(self, extra: Optional[dict] = None) -> dict:
        _extra = {"sub_logger": self.sub_logger_name}

        if extra is not None:
            # check if any key is already in extra
            for key in extra:
                if key in _extra:
                    raise ValueError(f"Key '{key}' is reserved for ActionSubLogger.")
            _extra.update(extra)
        return _extra

    def _command(self, command: str, value: Union[str, int, float, bool, None]):
        record = self.makeRecord(self.name, logging.NOTSET, "", 0, "", (), None, extra=self._extra({"command": {"command": command, "value": value}}))
        self.handle(record)

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, stacklevel=1):
        super()._log(level=level, msg=msg, args=args, exc_info=exc_info, extra=self._extra(extra), stack_info=stack_info, stacklevel=stacklevel)

    def _step_command(self):
        if self.steps is None:
            return
        calculated_progress = round(self.step / self.steps * 100)

        self._command("step", calculated_progress)

    @property
    def sub_logger_name(self) -> str:
        return self.name.replace(self._action_logger.action_log_key + ".", "")

    @property
    def title(self) -> str:
        return self._title

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

    def next_step(self):
        if self.step >= self.steps:
            return
        self.step += 1

    def finalize(self, success: bool = True, log_level: int = logging.INFO, msg: Optional[str] = None):
        if self.exited:
            raise ValueError("ActionSubLogger already exited.")
        self.step = self.steps
        if msg is not None:
            self.log(log_level, msg)

        self._command("finalize", success)
        self.exit()

    def exit(self):
        if self.exited:
            raise ValueError("ActionSubLogger already exited.")

        # remove handler
        for handler in self.handlers:
            self.removeHandler(handler)

        # remove logger from logger manager
        logging.root.manager.loggerDict.pop(self.name, None)

    @property
    def exited(self) -> bool:
        return not self.is_logger_exist(name=self.name)


class ActionLogger:
    _action_loggers: list["ActionLogger"] = []

    def __init__(self, action_log_key: str, websocket: Optional[WebSocket] = None):
        self.action_log_key = action_log_key
        self.websocket = websocket

        self._sub_logger: list[ActionSubLogger] = []

        # add action logger to action loggers
        self._action_loggers.append(self)

    def __del__(self):
        if not self.exited:
            asyncio.run(self.exit())

    @classmethod
    async def get_logger(cls, action_log_key: str) -> Optional["ActionLogger"]:
        for _action_logger in cls._action_loggers:
            if _action_logger.action_log_key == action_log_key:
                return _action_logger
        return None

    @classmethod
    async def wait_for_logger(cls,
                              action_log_key_or_request: Union[str, Request],
                              # log_level: Optional[int] = None,
                              # parent: Optional[logging.Logger] = logger,
                              # formatter: logging.Formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d - %H:%M:%S"),
                              timeout: int = 5,
                              ignore_not_found: bool = False) -> "ActionLogger":
        """
        Wait for action logger to be created by WebSocket connection. If action logger not found, a dummy logger will be created or an error will be raised.

        :param action_log_key_or_request: Action log key or request.
        :param timeout: Timeout in seconds.
        :param ignore_not_found: Ignore if action logger not found. If True, a dummy logger will be created.
        :return: Action logger.
        """

        if isinstance(action_log_key_or_request, Request):
            action_log_key = action_log_key_or_request.query_params.get("actionLogKey", None)
            if action_log_key is None:
                raise ValueError("No action log key provided.")
        elif isinstance(action_log_key_or_request, str):
            action_log_key = action_log_key_or_request
        else:
            raise ValueError("Invalid action log key or request.")

        # get action logger
        action_logger = None
        current_try = 0
        while current_try < timeout:
            action_logger = await cls.get_logger(action_log_key=action_log_key)

            # if action logger found, break
            if action_logger is not None:
                break
            current_try += 1
            logger.debug(f"[{current_try}/{timeout}] Waiting for action logger...")
            await asyncio.sleep(1)

        # check if action logger finally found
        if action_logger is None:
            if not ignore_not_found:
                raise ValueError("ActionLogger not found.")
            # create dummy logger and warn
            action_logger = ActionLogger(action_log_key="dummy")
            warnings.warn("ActionLogger not found. Created dummy logger.", RuntimeWarning)

        # # set log level
        # if log_level is None:
        #     if parent is None:
        #         log_level = logging.INFO
        #     else:
        #         log_level = parent.level
        # action_logger.setLevel(log_level)
        #
        # # set parent logger
        # action_logger.parent = parent
        #
        # # set formatter
        # for handler in action_logger.handlers:
        #     handler.setFormatter(formatter)

        return action_logger

    def new_sub_logger(self, sub_logger_name: str, sub_logger_title: Optional[str] = None) -> ActionSubLogger:
        try:
            self.get_sub_logger(sub_logger_name=sub_logger_name)
        except ValueError:
            pass
        # create sub logger
        sub_logger = ActionSubLogger(action_logger=self, name=sub_logger_name, title=sub_logger_title)
        self._sub_logger.append(sub_logger)
        return sub_logger

    def get_sub_logger(self, sub_logger_name: str) -> ActionSubLogger:
        if self.exited:
            raise ValueError("ActionLogger already exited.")

        # check if sub logger already exists
        for sub_logger in self._sub_logger:
            if sub_logger.sub_logger_name == sub_logger_name:
                return sub_logger
        raise ValueError("Sub logger not found.")

    # def sub_logger(self, sub_logger_name: str, sub_logger_title: Optional[str] = None) -> ActionSubLogger:
    #     raise NotImplementedError("Sub logger context manager not implemented.")

    async def exit(self):
        if self.exited:
            raise ValueError("ActionLogger already exited.")

        # exit sub loggers
        for sub_logger in self._sub_logger:
            if not sub_logger.exited:
                sub_logger.exit()

        # check if websocket is connected
        if self.websocket.client_state != WebSocketState.DISCONNECTED:
            # close websocket
            await self.websocket.close(code=1000)

        # remove action logger from action loggers
        self._action_loggers.remove(self)

    @property
    def exited(self) -> bool:
        return self not in self._action_loggers


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
        action_logger = await ActionLogger.get_logger(self.action_log_key)
        if action_logger is None:
            return

        # exit logger
        await action_logger.exit()


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
            text="Test Action - Normal")
    # confirmation="Möchtest du die Test Aktion durchführen?",
    # icon_class="fa-regular fa-network-wired",
    # submit_btn_text="Ja, fortsetzen",
    # submit_btn_class="btn-success")
    async def test_action_normal(self, request: Request, pk: list[str]) -> str:
        await asyncio.sleep(2)

        return "Test Aktion erfolgreich."

    @action(name="test_action_action_log",
            text="Test Action - Action Log")
    # confirmation="Möchtest du die Test Aktion durchführen?",
    # icon_class="fa-regular fa-network-wired",
    # submit_btn_text="Ja, fortsetzen",
    # submit_btn_class="btn-success")
    async def test_action_action_log(self, request: Request, pk: list[str]) -> str:
        action_logger = await ActionLogger.wait_for_logger(request)

        action_logger.new_sub_logger("sub_action_1", "Sub Action 1").steps = 3
        action_logger.get_sub_logger("sub_action_1").info("Test Aktion startet ...")
        action_logger.get_sub_logger("sub_action_1").debug("Debug")
        action_logger.get_sub_logger("sub_action_1").info("Test Aktion step 1")
        await asyncio.sleep(2)
        action_logger.get_sub_logger("sub_action_1").next_step()
        action_logger.get_sub_logger("sub_action_1").info("Test Aktion step 2")
        await asyncio.sleep(2)
        action_logger.get_sub_logger("sub_action_1").next_step()
        action_logger.get_sub_logger("sub_action_1").steps += 100
        for i in range(1, 100):
            action_logger.get_sub_logger("sub_action_1").info(f"Test Aktion step 2 - {i}")
            action_logger.get_sub_logger("sub_action_1").next_step()
            await asyncio.sleep(0.1)
        action_logger.get_sub_logger("sub_action_1").info("Test Aktion step 3")
        await asyncio.sleep(2)
        action_logger.get_sub_logger("sub_action_1").next_step()
        action_logger.get_sub_logger("sub_action_1").finalize(success=False, msg="Test Aktion fehlgeschlagen.")

        action_logger.new_sub_logger("sub_action_2", "Sub Action 2").steps = 1
        action_logger.get_sub_logger("sub_action_2").info("Test Aktion startet ...")
        await asyncio.sleep(0.5)
        action_logger.get_sub_logger("sub_action_2").finalize(success=False, msg="Test Aktion fehlgeschlagen.")

        action_logger.new_sub_logger("sub_action_3", "Sub Action 3").steps = 1
        action_logger.get_sub_logger("sub_action_3").info("Test Aktion startet ...")
        await asyncio.sleep(0.5)
        action_logger.get_sub_logger("sub_action_3").finalize(success=True, msg="Test Aktion erfolgreich.")

        action_logger.new_sub_logger("sub_action_4", "Sub Action 4").steps = 1
        action_logger.get_sub_logger("sub_action_4").info("Test Aktion startet ...")
        await asyncio.sleep(0.5)
        action_logger.get_sub_logger("sub_action_4").finalize(success=False, msg="Test Aktion fehlgeschlagen.")

        action_logger.new_sub_logger("sub_action_5", "Sub Action 5").steps = 1
        action_logger.get_sub_logger("sub_action_5").info("Test Aktion startet ...")
        await asyncio.sleep(0.5)
        action_logger.get_sub_logger("sub_action_5").finalize(success=True, msg="Test Aktion erfolgreich.")

        action_logger.new_sub_logger("sub_action_6", "Sub Action 6").steps = 1
        action_logger.get_sub_logger("sub_action_6").info("Test Aktion startet ...")
        await asyncio.sleep(0.5)
        action_logger.get_sub_logger("sub_action_6").finalize(success=False, msg="Test Aktion fehlgeschlagen.")

        action_logger.new_sub_logger("sub_action_7", "Sub Action 7").steps = 1
        action_logger.get_sub_logger("sub_action_7").info("Test Aktion startet ...")
        await asyncio.sleep(0.5)
        action_logger.get_sub_logger("sub_action_7").finalize(success=True, msg="Test Aktion erfolgreich.")

        action_logger.new_sub_logger("sub_action_8", "Sub Action 8").steps = 1
        action_logger.get_sub_logger("sub_action_8").info("Test Aktion startet ...")
        await asyncio.sleep(0.5)
        action_logger.get_sub_logger("sub_action_8").finalize(success=False, msg="Test Aktion fehlgeschlagen.")

        action_logger.new_sub_logger("sub_action_9", "Sub Action 9").steps = 1
        action_logger.get_sub_logger("sub_action_9").info("Test Aktion startet ...")
        await asyncio.sleep(0.5)
        action_logger.get_sub_logger("sub_action_9").finalize(success=True, msg="Test Aktion erfolgreich.")

        action_logger.new_sub_logger("sub_action_10", "Sub Action 10").steps = 1
        action_logger.get_sub_logger("sub_action_10").info("Test Aktion startet ...")
        await asyncio.sleep(0.5)
        action_logger.get_sub_logger("sub_action_10").finalize(success=False, msg="Test Aktion fehlgeschlagen.")

        action_logger.new_sub_logger("sub_action_11", "Sub Action 11").steps = 1
        action_logger.get_sub_logger("sub_action_11").info("Test Aktion startet ...")
        await asyncio.sleep(0.5)
        action_logger.get_sub_logger("sub_action_11").finalize(success=True, msg="Test Aktion erfolgreich.")

        action_logger.new_sub_logger("sub_action_12", "Sub Action 12").steps = 1
        action_logger.get_sub_logger("sub_action_12").info("Test Aktion startet ...")
        await asyncio.sleep(0.5)
        action_logger.get_sub_logger("sub_action_12").finalize(success=False, msg="Test Aktion fehlgeschlagen.")

        action_logger.new_sub_logger("sub_action_13", "Sub Action 13").steps = 1
        action_logger.get_sub_logger("sub_action_13").info("Test Aktion startet ...")
        await asyncio.sleep(0.5)
        action_logger.get_sub_logger("sub_action_13").finalize(success=True, msg="Test Aktion erfolgreich.")

        action_logger.new_sub_logger("sub_action_14", "Sub Action 14").steps = 1
        action_logger.get_sub_logger("sub_action_14").info("Test Aktion startet ...")
        await asyncio.sleep(0.5)
        action_logger.get_sub_logger("sub_action_14").finalize(success=False, msg="Test Aktion fehlgeschlagen.")

        action_logger.new_sub_logger("sub_action_15", "Sub Action 15").steps = 1
        action_logger.get_sub_logger("sub_action_15").info("Test Aktion startet ...")
        await asyncio.sleep(0.5)
        action_logger.get_sub_logger("sub_action_15").finalize(success=True, msg="Test Aktion erfolgreich.")

        action_logger.new_sub_logger("sub_action_16", "Sub Action 16").steps = 1
        action_logger.get_sub_logger("sub_action_16").info("Test Aktion startet ...")
        await asyncio.sleep(0.5)
        action_logger.get_sub_logger("sub_action_16").finalize(success=False, msg="Test Aktion fehlgeschlagen.")

        action_logger.new_sub_logger("sub_action_17", "Sub Action 17").steps = 1
        action_logger.get_sub_logger("sub_action_17").info("Test Aktion startet ...")
        await asyncio.sleep(0.5)
        action_logger.get_sub_logger("sub_action_17").finalize(success=True, msg="Test Aktion erfolgreich.")

        action_logger.new_sub_logger("sub_action_18", "Sub Action 18").steps = 1
        action_logger.get_sub_logger("sub_action_18").info("Test Aktion startet ...")
        await asyncio.sleep(0.5)
        action_logger.get_sub_logger("sub_action_18").finalize(success=False, msg="Test Aktion fehlgeschlagen.")

        action_logger.new_sub_logger("sub_action_19", "Sub Action 19").steps = 1
        action_logger.get_sub_logger("sub_action_19").info("Test Aktion startet ...")
        await asyncio.sleep(0.5)
        action_logger.get_sub_logger("sub_action_19").finalize(success=True, msg="Test Aktion erfolgreich.")

        action_logger.new_sub_logger("sub_action_20", "Sub Action 20").steps = 1
        action_logger.get_sub_logger("sub_action_20").info("Test Aktion startet ...")
        await asyncio.sleep(0.5)
        action_logger.get_sub_logger("sub_action_20").finalize(success=False, msg="Test Aktion fehlgeschlagen.")

        return "Test Aktion erfolgreich."


# Add views to admin#
admin.add_view(TestView())

# Mount admin to app
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
