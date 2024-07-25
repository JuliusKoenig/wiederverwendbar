import json
import logging
import asyncio
import string
import traceback
import warnings
from typing import Optional, Union, Sequence

import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import HTMLResponse
from starlette.routing import Route, WebSocketRoute
from starlette.requests import Request
from starlette.endpoints import WebSocketEndpoint
from starlette.websockets import WebSocket, WebSocketState
from starlette_admin import CustomView, I18nConfig
from starlette_admin.auth import BaseAuthProvider
from starlette_admin.base import BaseAdmin
from starlette_admin.contrib.mongoengine import Admin, ModelView
from starlette_admin.actions import action
from starlette_admin.exceptions import ActionFailed
from starlette_admin.i18n import lazy_gettext as _
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
    def __init__(self):
        super().__init__()

        self.global_buffer: list[logging.LogRecord] = []  # global_buffer
        self.websockets: dict[WebSocket, list[logging.LogRecord]] = {}  # websocket, websocket_buffer

    def send(self, websocket: WebSocket, record: logging.LogRecord):
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

        # check websocket is connected
        if websocket.client_state != WebSocketState.CONNECTED:
            warnings.warn("Websocket is not connected.")
            return

        # send command message
        try:
            asyncio.run(websocket.send_text(command_json))
        except Exception:
            self.handleError(record)

    def send_all(self):
        # send buffered records
        for websocket in self.websockets:
            while self.websockets[websocket]:
                buffered_record = self.websockets[websocket].pop(0)
                self.send(websocket, buffered_record)

    def emit(self, record: logging.LogRecord) -> None:
        # add record to global buffer
        self.global_buffer.append(record)

        # add record to websocket buffer
        for websocket in self.websockets:
            self.websockets[websocket].append(record)

        # send all
        self.send_all()

    def add_websocket(self, websocket: WebSocket):
        # check if websocket already exists
        if websocket in self.websockets:
            raise ValueError("Websocket already exists.")

        # add websocket to websocket buffer
        self.websockets[websocket] = []

        # push all global buffer to websocket buffer
        for record in self.global_buffer:
            self.websockets[websocket].append(record)

        # send all
        self.send_all()

    def remove_websocket(self, websocket: WebSocket):
        # check if websocket exists
        if websocket not in self.websockets:
            raise ValueError("Websocket not exists.")

        # send all
        self.send_all()

        # remove websocket from websocket buffer
        self.websockets.pop(websocket)


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
        self._websockets: list[WebSocket] = []

        # check if logger already exists
        if self.is_logger_exist(name=self.name):
            raise ValueError("ActionSubLogger already exists.")

        # create websocket handler
        websocket_handler = WebsocketHandler()
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

    def add_websocket(self, websocket: WebSocket):
        # add websocket to websocket handler
        for handler in self.handlers:
            if not isinstance(handler, WebsocketHandler):
                continue
            handler.add_websocket(websocket)

        # add websocket to sub logger
        if websocket in self._websockets:
            return
        self._websockets.append(websocket)

    def remove_websocket(self, websocket: WebSocket):
        # remove websocket from sub logger
        for handler in self.handlers:
            if not isinstance(handler, WebsocketHandler):
                continue
            handler.remove_websocket(websocket)

        # remove websocket from sub logger
        if websocket not in self._websockets:
            return
        self._websockets.remove(websocket)

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
        if success and self.step < self.steps:
            self.step = self.steps
        if msg is not None:
            self.log(log_level, msg)

        self._command("finalize", success)
        self.exit()

    def exit(self):
        if self.exited:
            raise ValueError("ActionSubLogger already exited.")

        # remove websockets
        for websocket in self._websockets:
            self.remove_websocket(websocket)

        # remove handler
        for handler in self.handlers:
            self.removeHandler(handler)

        # remove logger from logger manager
        logging.root.manager.loggerDict.pop(self.name, None)

    @property
    def exited(self) -> bool:
        return not self.is_logger_exist(name=self.name)


class ActionLogger:
    class ActionSubLoggerContext:
        def __init__(self,
                     action_logger: "ActionLogger",
                     name: str,
                     title: Optional[str] = None,
                     log_level: Optional[int] = None,
                     parent: Optional[logging.Logger] = None,
                     formatter: Optional[logging.Formatter] = None,
                     steps: Optional[int] = None,
                     finalize_on_success_log_level: int = logging.INFO,
                     finalize_on_success_msg: Optional[str] = None,
                     show_errors: Optional[bool] = None):
            # create sub logger
            self.sub_logger = action_logger.new_sub_logger(name=name, title=title, log_level=log_level, parent=parent, formatter=formatter, steps=steps)

            self.finalize_on_success_log_level = finalize_on_success_log_level
            self.finalize_on_success_msg = finalize_on_success_msg
            if show_errors is None:
                show_errors = action_logger.show_errors
            self.show_errors = show_errors

        def __enter__(self) -> "ActionSubLogger":
            return self.sub_logger

        def __exit__(self, exc_type, exc_val, exc_tb):
            if not self.sub_logger.exited:
                if exc_type is None:
                    self.sub_logger.finalize(success=True, log_level=self.finalize_on_success_log_level, msg=self.finalize_on_success_msg)
                else:
                    if self.show_errors:
                        # get exception string
                        tb_str = traceback.format_exc()
                        self.sub_logger.finalize(success=False, log_level=logging.ERROR, msg=tb_str)
                    else:
                        self.sub_logger.finalize(success=False, log_level=logging.ERROR, msg="Something went wrong.")

    _action_loggers: list["ActionLogger"] = []

    def __init__(self,
                 action_log_key_request_or_websocket: Union[str, Request],
                 log_level: Optional[int] = None,
                 parent: Optional[logging.Logger] = None,
                 formatter: Optional[logging.Formatter] = None,
                 show_errors: bool = True,
                 wait_for_websocket: bool = True,
                 wait_for_websocket_timeout: int = 5):
        """
        Create new action logger.

        :param action_log_key_request_or_websocket: Action log key, request or websocket.
        :param log_level: Log level of action logger. If None, parent log level will be used. If parent is None, logging.INFO will be used.
        :param parent: Parent logger. If None, logger will be added to module logger.
        :param formatter: Formatter of action logger. If None, default formatter will be used.
        """

        self.action_log_key = self.get_action_key(action_log_key_request_or_websocket)
        self.show_errors = show_errors
        if log_level is None:
            if parent is None:
                log_level = logging.INFO
            else:
                log_level = parent.level
        self.log_level = log_level
        if parent is None:
            parent = logger
        self.parent = parent
        if formatter is None:
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d - %H:%M:%S")
        self.formatter = formatter

        self._websockets: list[WebSocket] = []
        self._sub_logger: list[ActionSubLogger] = []

        # add action logger to action loggers
        self._action_loggers.append(self)

        # wait for websocket
        if wait_for_websocket:
            current_try = 0
            while len(self._websockets) == 0:
                if current_try >= wait_for_websocket_timeout:
                    raise ValueError("No websocket connected.")
                current_try += 1
                logger.debug(f"[{current_try}/{wait_for_websocket_timeout}] Waiting for websocket...")
                asyncio.run(asyncio.sleep(1))

    def __enter__(self) -> "ActionLogger":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.exited:
            self.exit()

        # get exception string
        if exc_type is not None and self.show_errors:
            exception_str = f"{exc_type.__name__}: {exc_val}"
            # add line number
            if exc_tb is not None:
                exception_str += f" at line {exc_tb.tb_lineno} in {exc_tb.tb_frame.f_code.co_filename}"

            # raise ActionFailed
            raise ActionFailed(exception_str)

    def __del__(self):
        if not self.exited:
            self.exit()

    @classmethod
    async def get_logger(cls, action_log_key_request_or_websocket: Union[str, Request, WebSocket]) -> Optional["ActionLogger"]:
        """
        Get action logger by action log key or request.

        :param action_log_key_request_or_websocket: Action log key, request or websocket.
        :return: Action logger.
        """

        for _action_logger in cls._action_loggers:
            if _action_logger.action_log_key == cls.get_action_key(action_log_key_request_or_websocket):
                return _action_logger
        return None

    @classmethod
    def get_action_key(cls, action_log_key_request_or_websocket: Union[str, Request, WebSocket]):
        """
        Get action log key from request or websocket.

        :param action_log_key_request_or_websocket: Action log key, request or websocket.
        :return: Action log key.
        """

        if isinstance(action_log_key_request_or_websocket, Request):
            action_log_key = action_log_key_request_or_websocket.query_params.get("actionLogKey", None)
            if action_log_key is None:
                raise ValueError("No action log key provided.")
        elif isinstance(action_log_key_request_or_websocket, WebSocket):
            action_log_key = action_log_key_request_or_websocket.path_params.get("action_log_key", None)
            if action_log_key is None:
                raise ValueError("No action log key provided.")
        elif isinstance(action_log_key_request_or_websocket, str):
            action_log_key = action_log_key_request_or_websocket
        else:
            raise ValueError("Invalid action log key or request.")
        return action_log_key

    @classmethod
    async def wait_for_logger(cls, action_log_key_request_or_websocket: Union[str, Request, WebSocket], timeout: int = 5) -> "ActionLogger":
        """
        Wait for action logger to be created by WebSocket connection. If action logger not found, a dummy logger will be created or an error will be raised.

        :param action_log_key_request_or_websocket: Action log key, request or websocket.
        :param timeout: Timeout in seconds.
        :return: Action logger.
        """

        # get action logger
        action_logger = None
        current_try = 0
        while current_try < timeout:
            action_logger = await cls.get_logger(cls.get_action_key(action_log_key_request_or_websocket))

            # if action logger found, break
            if action_logger is not None:
                break
            current_try += 1
            logger.debug(f"[{current_try}/{timeout}] Waiting for action logger...")
            await asyncio.sleep(1)

        # check if action logger finally found
        if action_logger is None:
            raise ValueError("ActionLogger not found.")

        return action_logger

    def add_websocket(self, websocket: WebSocket):
        # add websocket to sub loggers
        for sub_logger in self._sub_logger:
            sub_logger.add_websocket(websocket)

        # add websocket to action logger
        if websocket in self._websockets:
            return
        self._websockets.append(websocket)

    def remove_websocket(self, websocket: WebSocket):
        # remove websocket from sub loggers
        for sub_logger in self._sub_logger:
            sub_logger.remove_websocket(websocket)

        # remove websocket from action logger
        if websocket not in self._websockets:
            return
        self._websockets.remove(websocket)

    def new_sub_logger(self,
                       name: str,
                       title: Optional[str] = None,
                       log_level: Optional[int] = None,
                       parent: Optional[logging.Logger] = None,
                       formatter: Optional[logging.Formatter] = None,
                       steps: Optional[int] = None) -> ActionSubLogger:
        """
        Create new sub logger.

        :param name: Name of sub logger. Only a-z, A-Z, 0-9, - and _ are allowed.
        :param title: Title of sub logger. Visible in frontend.
        :param log_level: Log level of sub logger. If None, parent log level will be used. If parent is None, action logger log level will be used.
        :param parent: Parent logger. If None, action logger parent will be used.
        :param formatter: Formatter of sub logger. If None, action logger formatter will be used.
        :param steps: Steps of sub logger. If None, no steps will be shown.
        :return:
        """

        try:
            self.get_sub_logger(sub_logger_name=name)
        except ValueError:
            pass

        # create sub logger
        sub_logger = ActionSubLogger(action_logger=self, name=name, title=title)

        # set log level
        if log_level is None:
            if parent is None:
                log_level = self.log_level
            else:
                log_level = parent.level
        sub_logger.setLevel(log_level)

        # set parent logger
        if parent is None:
            parent = self.parent
        sub_logger.parent = parent

        # set formatter
        if formatter is None:
            formatter = self.formatter
        for handler in sub_logger.handlers:
            handler.setFormatter(formatter)

        # set steps
        if steps is not None:
            sub_logger.steps = steps

        # add websocket to sub logger
        for websocket in self._websockets:
            sub_logger.add_websocket(websocket)

        self._sub_logger.append(sub_logger)
        return sub_logger

    def get_sub_logger(self, sub_logger_name: str) -> ActionSubLogger:
        """
        Get sub logger by name.

        :param sub_logger_name: Name of sub logger.
        :return:
        """

        if self.exited:
            raise ValueError("ActionLogger already exited.")

        # check if sub logger already exists
        for sub_logger in self._sub_logger:
            if sub_logger.sub_logger_name == sub_logger_name:
                return sub_logger
        raise ValueError("Sub logger not found.")

    def sub_logger(self,
                   name: str,
                   title: Optional[str] = None,
                   log_level: Optional[int] = None,
                   parent: Optional[logging.Logger] = None,
                   formatter: Optional[logging.Formatter] = None,
                   steps: Optional[int] = None,
                   finalize_on_success_log_level: int = logging.INFO,
                   finalize_on_success_msg: Optional[str] = None,
                   show_errors: Optional[bool] = None) -> ActionSubLoggerContext:
        """
        Sub logger context manager.

        :param name: Name of sub logger. Only a-z, A-Z, 0-9, - and _ are allowed.
        :param title: Title of sub logger. Visible in frontend.
        :param log_level: Log level of sub logger. If None, parent log level will be used. If parent is None, action logger log level will be used.
        :param parent: Parent logger. If None, action logger parent will be used.
        :param formatter: Formatter of sub logger. If None, action logger formatter will be used.
        :param steps: Steps of sub logger.
        :param finalize_on_success_log_level: Log level of finalize message if success.
        :param finalize_on_success_msg: Message of finalize message if success.
        :param show_errors: Show errors in frontend. If None, action logger show_errors will be used.
        :return:
        """

        return self.ActionSubLoggerContext(action_logger=self,
                                           name=name,
                                           title=title,
                                           log_level=log_level,
                                           parent=parent,
                                           formatter=formatter,
                                           steps=steps,
                                           finalize_on_success_log_level=finalize_on_success_log_level,
                                           finalize_on_success_msg=finalize_on_success_msg,
                                           show_errors=show_errors)

    def exit(self):
        """
        Exit action logger.

        :return: None
        """

        if self.exited:
            raise ValueError("ActionLogger already exited.")

        # remove websockets
        for websocket in self._websockets:
            self.remove_websocket(websocket)

        # exit sub loggers
        for sub_logger in self._sub_logger:
            if not sub_logger.exited:
                sub_logger.exit()

        # remove action logger from action loggers
        self._action_loggers.remove(self)

    @property
    def exited(self) -> bool:
        """
        Check if action logger is exited.

        :return: True if exited, otherwise False.
        """

        return self not in self._action_loggers


class ActionLogEndpoint(WebSocketEndpoint):
    encoding = "text"
    wait_for_logger_timeout = 5

    async def on_connect(self, websocket: WebSocket):
        await websocket.accept()

        # wait for action logger
        try:
            action_logger = await ActionLogger.wait_for_logger(websocket, timeout=self.wait_for_logger_timeout)
        except Exception as e:
            await websocket.close(code=1008)
            raise e

        # add websocket to action logger
        action_logger.add_websocket(websocket)

    async def on_disconnect(self, websocket: WebSocket, close_code: int):
        # get logger
        action_logger = await ActionLogger.get_logger(websocket)
        if action_logger is None:
            return

        # remove websocket from logger
        action_logger.remove_websocket(websocket)


class CustomActionAdmin(BaseAdmin):
    def __init__(
            self,
            title: str = _("Admin"),
            base_url: str = "/admin",
            route_name: str = "admin",
            logo_url: Optional[str] = None,
            login_logo_url: Optional[str] = None,
            templates_dir: str = "templates",
            statics_dir: Optional[str] = None,
            index_view: Optional[CustomView] = None,
            auth_provider: Optional[BaseAuthProvider] = None,
            middlewares: Optional[Sequence[Middleware]] = None,
            debug: bool = False,
            i18n_config: Optional[I18nConfig] = None,
            favicon_url: Optional[str] = None,
            action_log_endpoint: type[ActionLogEndpoint] = ActionLogEndpoint,
    ):
        self.action_log_endpoint = action_log_endpoint
        super().__init__(title=title,
                         base_url=base_url,
                         route_name=route_name,
                         logo_url=logo_url,
                         login_logo_url=login_logo_url,
                         templates_dir=templates_dir,
                         statics_dir=statics_dir,
                         index_view=index_view,
                         auth_provider=auth_provider,
                         middlewares=middlewares,
                         debug=debug,
                         i18n_config=i18n_config,
                         favicon_url=favicon_url)

    def init_routes(self) -> None:
        super().init_routes()
        self.routes.append(WebSocketRoute(path="/ws/action_log/{action_log_key}", endpoint=self.action_log_endpoint, name="action_log"))  # noqa


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
        with ActionLogger(request) as action_logger:
            with action_logger.sub_logger("sub_action_1", "Sub Action 1") as sub_logger:
                _ = 1 / 0
                sub_logger.steps = 3
                sub_logger.info("Test Aktion startet ...")
                sub_logger.debug("Debug")
                sub_logger.info("Test Aktion step 1")
                await asyncio.sleep(2)
                sub_logger.next_step()
                sub_logger.info("Test Aktion step 2")
                await asyncio.sleep(2)
                sub_logger.next_step()
                sub_logger.steps += 100
                for i in range(1, 100):
                    sub_logger.info(f"Test Aktion step 2 - {i}")
                    sub_logger.next_step()
                    await asyncio.sleep(0.1)
                sub_logger.info("Test Aktion step 3")
                await asyncio.sleep(2)
                sub_logger.next_step()
                sub_logger.finalize(success=False, msg="Test Aktion fehlgeschlagen.")

            action_logger.new_sub_logger("sub_action_2", "Sub Action 2").steps = 3
            action_logger.new_sub_logger("sub_action_3", "Sub Action 3").steps = 3
            action_logger.get_sub_logger("sub_action_2").info("Test Aktion startet ...")
            action_logger.get_sub_logger("sub_action_3").info("Test Aktion startet ...")
            await asyncio.sleep(2)
            action_logger.get_sub_logger("sub_action_2").next_step()
            action_logger.get_sub_logger("sub_action_3").next_step()
            await asyncio.sleep(2)
            action_logger.get_sub_logger("sub_action_2").next_step()
            action_logger.get_sub_logger("sub_action_3").next_step()
            action_logger.get_sub_logger("sub_action_2").finalize(success=False, msg="Test Aktion fehlgeschlagen.")
            action_logger.get_sub_logger("sub_action_3").finalize(success=True, msg="Test Aktion erfolgreich.")

            # action_logger.new_sub_logger("sub_action_4", "Sub Action 4").steps = 1
            # action_logger.get_sub_logger("sub_action_4").info("Test Aktion startet ...")
            # await asyncio.sleep(0.5)
            # action_logger.get_sub_logger("sub_action_4").finalize(success=False, msg="Test Aktion fehlgeschlagen.")
            #
            # action_logger.new_sub_logger("sub_action_5", "Sub Action 5").steps = 1
            # action_logger.get_sub_logger("sub_action_5").info("Test Aktion startet ...")
            # await asyncio.sleep(0.5)
            # action_logger.get_sub_logger("sub_action_5").finalize(success=True, msg="Test Aktion erfolgreich.")
            #
            # action_logger.new_sub_logger("sub_action_6", "Sub Action 6").steps = 1
            # action_logger.get_sub_logger("sub_action_6").info("Test Aktion startet ...")
            # await asyncio.sleep(0.5)
            # action_logger.get_sub_logger("sub_action_6").finalize(success=False, msg="Test Aktion fehlgeschlagen.")
            #
            # action_logger.new_sub_logger("sub_action_7", "Sub Action 7").steps = 1
            # action_logger.get_sub_logger("sub_action_7").info("Test Aktion startet ...")
            # await asyncio.sleep(0.5)
            # action_logger.get_sub_logger("sub_action_7").finalize(success=True, msg="Test Aktion erfolgreich.")
            #
            # action_logger.new_sub_logger("sub_action_8", "Sub Action 8").steps = 1
            # action_logger.get_sub_logger("sub_action_8").info("Test Aktion startet ...")
            # await asyncio.sleep(0.5)
            # action_logger.get_sub_logger("sub_action_8").finalize(success=False, msg="Test Aktion fehlgeschlagen.")
            #
            # action_logger.new_sub_logger("sub_action_9", "Sub Action 9").steps = 1
            # action_logger.get_sub_logger("sub_action_9").info("Test Aktion startet ...")
            # await asyncio.sleep(0.5)
            # action_logger.get_sub_logger("sub_action_9").finalize(success=True, msg="Test Aktion erfolgreich.")
            #
            # action_logger.new_sub_logger("sub_action_10", "Sub Action 10").steps = 1
            # action_logger.get_sub_logger("sub_action_10").info("Test Aktion startet ...")
            # await asyncio.sleep(0.5)
            # action_logger.get_sub_logger("sub_action_10").finalize(success=False, msg="Test Aktion fehlgeschlagen.")
            #
            # action_logger.new_sub_logger("sub_action_11", "Sub Action 11").steps = 1
            # action_logger.get_sub_logger("sub_action_11").info("Test Aktion startet ...")
            # await asyncio.sleep(0.5)
            # action_logger.get_sub_logger("sub_action_11").finalize(success=True, msg="Test Aktion erfolgreich.")
            #
            # action_logger.new_sub_logger("sub_action_12", "Sub Action 12").steps = 1
            # action_logger.get_sub_logger("sub_action_12").info("Test Aktion startet ...")
            # await asyncio.sleep(0.5)
            # action_logger.get_sub_logger("sub_action_12").finalize(success=False, msg="Test Aktion fehlgeschlagen.")
            #
            # action_logger.new_sub_logger("sub_action_13", "Sub Action 13").steps = 1
            # action_logger.get_sub_logger("sub_action_13").info("Test Aktion startet ...")
            # await asyncio.sleep(0.5)
            # action_logger.get_sub_logger("sub_action_13").finalize(success=True, msg="Test Aktion erfolgreich.")
            #
            # action_logger.new_sub_logger("sub_action_14", "Sub Action 14").steps = 1
            # action_logger.get_sub_logger("sub_action_14").info("Test Aktion startet ...")
            # await asyncio.sleep(0.5)
            # action_logger.get_sub_logger("sub_action_14").finalize(success=False, msg="Test Aktion fehlgeschlagen.")
            #
            # action_logger.new_sub_logger("sub_action_15", "Sub Action 15").steps = 1
            # action_logger.get_sub_logger("sub_action_15").info("Test Aktion startet ...")
            # await asyncio.sleep(0.5)
            # action_logger.get_sub_logger("sub_action_15").finalize(success=True, msg="Test Aktion erfolgreich.")
            #
            # action_logger.new_sub_logger("sub_action_16", "Sub Action 16").steps = 1
            # action_logger.get_sub_logger("sub_action_16").info("Test Aktion startet ...")
            # await asyncio.sleep(0.5)
            # action_logger.get_sub_logger("sub_action_16").finalize(success=False, msg="Test Aktion fehlgeschlagen.")
            #
            # action_logger.new_sub_logger("sub_action_17", "Sub Action 17").steps = 1
            # action_logger.get_sub_logger("sub_action_17").info("Test Aktion startet ...")
            # await asyncio.sleep(0.5)
            # action_logger.get_sub_logger("sub_action_17").finalize(success=True, msg="Test Aktion erfolgreich.")
            #
            # action_logger.new_sub_logger("sub_action_18", "Sub Action 18").steps = 1
            # action_logger.get_sub_logger("sub_action_18").info("Test Aktion startet ...")
            # await asyncio.sleep(0.5)
            # action_logger.get_sub_logger("sub_action_18").finalize(success=False, msg="Test Aktion fehlgeschlagen.")
            #
            # action_logger.new_sub_logger("sub_action_19", "Sub Action 19").steps = 1
            # action_logger.get_sub_logger("sub_action_19").info("Test Aktion startet ...")
            # await asyncio.sleep(0.5)
            # action_logger.get_sub_logger("sub_action_19").finalize(success=True, msg="Test Aktion erfolgreich.")
            #
            # action_logger.new_sub_logger("sub_action_20", "Sub Action 20").steps = 1
            # action_logger.get_sub_logger("sub_action_20").info("Test Aktion startet ...")
            # await asyncio.sleep(0.5)
            # action_logger.get_sub_logger("sub_action_20").finalize(success=False, msg="Test Aktion fehlgeschlagen.")

        return "Test Aktion erfolgreich."


# Add views to admin#
admin.add_view(TestView())

# Mount admin to app
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
