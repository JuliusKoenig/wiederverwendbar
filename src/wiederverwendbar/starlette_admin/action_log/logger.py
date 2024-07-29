import json
import logging
import asyncio
import string
import traceback
import warnings
from typing import Optional, Union

from starlette.requests import Request
from starlette.websockets import WebSocket, WebSocketState
from starlette_admin.exceptions import ActionFailed

from wiederverwendbar.logger.logger_context import LoggingContext

logger = logging.getLogger(__name__)


class WebsocketHandler(logging.Handler):
    def __init__(self):
        """
        Create new websocket handler.

        :return: None
        """

        super().__init__()

        self.global_buffer: list[logging.LogRecord] = []  # global_buffer
        self.websockets: dict[WebSocket, list[logging.LogRecord]] = {}  # websocket, websocket_buffer

    def send(self, websocket: WebSocket, record: logging.LogRecord) -> None:
        """
        Send log record to websocket.

        :param websocket: Websocket
        :param record: Log record
        :return: None
        """

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

    def send_all(self) -> None:
        """
        Send all buffered records to all websockets.

        :return: None
        """

        # send buffered records
        for websocket in self.websockets:
            while self.websockets[websocket]:
                buffered_record = self.websockets[websocket].pop(0)
                self.send(websocket, buffered_record)

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit log record.

        :param record: Log record
        :return: None
        """

        # add record to global buffer
        self.global_buffer.append(record)

        # add record to websocket buffer
        for websocket in self.websockets:
            self.websockets[websocket].append(record)

        # send all
        self.send_all()

    def add_websocket(self, websocket: WebSocket):
        """
        Add websocket to websocket handler. All global buffer will be sent to websocket buffer. After that, all buffered records will be sent to websocket.

        :param websocket: Websocket
        :return: None
        """

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
        """
        Remove websocket from websocket handler. All buffered records will be sent to websocket.
        :param websocket: Websocket
        :return: None
        """

        # check if websocket exists
        if websocket not in self.websockets:
            raise ValueError("Websocket not exists.")

        # send all
        self.send_all()

        # remove websocket from websocket buffer
        self.websockets.pop(websocket)


class ActionSubLogger(logging.Logger):
    def __init__(self, action_logger: "ActionLogger", name: str, title: Optional[str] = None):
        """
        Create new action sub logger.

        :param action_logger: Action logger
        :param name: Name of sub logger. Only a-z, A-Z, 0-9, - and _ are allowed.
        :param title: Title of sub logger. Visible in frontend.
        """

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
        """
        Get logger by name.

        :param name: Name of logger.
        :return: Logger
        """

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
        """
        Check if logger exists by name.

        :param name: Name of logger.
        :return: True if exists, otherwise False.
        """

        return cls._get_logger(name=name) is not None

    def _extra(self, extra: Optional[dict] = None) -> dict:
        """
        Add extra to log record and check if any key is already in extra.

        :param extra: Extra of log record.
        :return: New extra.
        """

        _extra = {"sub_logger": self.sub_logger_name}

        if extra is not None:
            # check if any key is already in extra
            for key in extra:
                if key in _extra:
                    raise ValueError(f"Key '{key}' is reserved for ActionSubLogger.")
            _extra.update(extra)
        return _extra

    def _command(self, command: str, value: Union[str, int, float, bool, None]) -> None:
        """
        Send command to websocket.

        :param command: Command
        :param value: Value
        :return: None
        """

        record = self.makeRecord(self.name, logging.NOTSET, "", 0, "", (), None, extra=self._extra({"command": {"command": command, "value": value}}))
        self.handle(record)

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, stacklevel=1) -> None:
        """
        Log message.

        :param level: Log level
        :param msg: Message
        :param args: Arguments
        :param exc_info: Exception info
        :param extra: Extra added to log record
        :param stack_info: Stack info
        :param stacklevel: Stack level
        :return: None
        """

        super()._log(level=level, msg=msg, args=args, exc_info=exc_info, extra=self._extra(extra), stack_info=stack_info, stacklevel=stacklevel)

    def _step_command(self) -> None:
        """
        Send step command to websocket.

        :return: None
        """

        if self.steps is None:
            return
        calculated_progress = round(self.step / self.steps * 100)

        self._command("step", calculated_progress)

    def add_websocket(self, websocket: WebSocket) -> None:
        """
        Add websocket to sub logger.

        :param websocket: Websocket
        :return: None
        """

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
        """
        Remove websocket from sub logger.

        :param websocket: Websocket
        :return: None
        """

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
        """
        Get sub logger name.

        :return: Sub logger name.
        """

        return self.name.replace(self._action_logger.action_log_key + ".", "")

    @property
    def title(self) -> str:
        """
        Get title of sub logger.

        :return: Title of sub logger.
        """

        return self._title

    @property
    def steps(self) -> int:
        """
        Get steps of sub logger.

        :return: Steps of sub logger.
        """

        return self._steps

    @steps.setter
    def steps(self, value: int) -> None:
        """
        Set steps of sub logger. Also send step command to websocket.

        :param value: Steps
        :return: None
        """

        if value < 0:
            raise ValueError("Steps must be greater than 0.")
        self._steps = value
        self._step_command()

    @property
    def step(self) -> int:
        """
        Get step of sub logger.

        :return: Step of sub logger.
        """
        return self._step

    @step.setter
    def step(self, value: int) -> None:
        """
        Set step of sub logger. Also send step command to websocket.

        :param value: Step
        :return: None
        """

        self._step = value
        self._step_command()

    def next_step(self) -> None:
        """
        Increase step by 1.

        :return: None
        """

        if self.step >= self.steps:
            return
        self.step += 1

    def finalize(self, success: bool = True, log_level: int = logging.INFO, msg: Optional[str] = None) -> None:
        """
        Finalize sub logger. Also send finalize command to websocket.

        :param success: If True, frontend will show success message. If False, frontend will show error message.
        :param log_level: Log level of finalize message.
        :param msg: Message of finalize message.
        :return: None
        """

        if self.exited:
            raise ValueError("ActionSubLogger already exited.")

        if success:
            if self.steps is not None:
                if self.step < self.steps:
                    self.step = self.steps
        if msg is not None:
            self.log(log_level, msg)

        self._command("finalize", success)
        self.exit()

    def exit(self) -> None:
        """
        Exit sub logger. Also remove websocket from sub logger.

        :return: None
        """

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
        """
        Check if sub logger is exited.

        :return: True if exited, otherwise False.
        """

        return not self.is_logger_exist(name=self.name)


class ActionSubLoggerContext(LoggingContext):
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
                 show_errors: Optional[bool] = None,
                 handle_origin_logger: bool = True):
        """
        Create new action sub logger context manager.

        :param action_logger: Action logger
        :param name: Name of sub logger. Only a-z, A-Z, 0-9, - and _ are allowed.
        :param title: Title of sub logger. Visible in frontend.
        :param log_level: Log level of sub logger. If None, parent log level will be used. If parent is None, action logger log level will be used.
        :param parent: Parent logger. If None, action logger parent will be used.
        :param formatter: Formatter of sub logger. If None, action logger formatter will be used.
        :param steps: Steps of sub logger.
        :param finalize_on_success_log_level: Log level of finalize message if success.
        :param finalize_on_success_msg: Message of finalize message if success.
        :param show_errors: Show errors in frontend. If None, action logger show_errors will be used.
        :param handle_origin_logger: Handle origin logger.
        """

        # create sub logger
        self.context_logger = action_logger.new_sub_logger(name=name, title=title, log_level=log_level, parent=parent, formatter=formatter, steps=steps)

        self.finalize_on_success_log_level = finalize_on_success_log_level
        self.finalize_on_success_msg = finalize_on_success_msg
        if show_errors is None:
            show_errors = action_logger.show_errors
        self.show_errors = show_errors

        super().__init__(context_logger=self.context_logger, handle_origin_logger=handle_origin_logger)

    def __enter__(self) -> "ActionSubLogger":
        super().__enter__()
        return self.context_logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)
        if not self.context_logger.exited:
            if exc_type is None:
                self.context_logger.finalize(success=True, log_level=self.finalize_on_success_log_level, msg=self.finalize_on_success_msg)
            else:
                if self.show_errors:
                    # get exception string
                    tb_str = traceback.format_exc()
                    self.context_logger.finalize(success=False, log_level=logging.ERROR, msg=tb_str)
                else:
                    self.context_logger.finalize(success=False, log_level=logging.ERROR, msg="Something went wrong.")


class ActionLogger:
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

        # get parent logger
        if parent is None:
            parent = logger
        self.parent = parent

        # set log level
        if log_level is None:
            if parent is None:
                log_level = logging.INFO
            else:
                log_level = parent.level
        self.log_level = log_level

        # set formatter
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
            te = traceback.TracebackException(type(exc_type), exc_val, exc_tb)
            efs = te.stack[-1]
            exception_str = f"{exc_type.__name__}: {exc_val}"
            # add line number
            if exc_tb is not None:
                exception_str += f" at line {efs.lineno} in {efs.filename}"

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
    def get_action_key(cls, action_log_key_request_or_websocket: Union[str, Request, WebSocket]) -> str:
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

    def add_websocket(self, websocket: WebSocket) -> None:
        """
        Add websocket to action logger.

        :param websocket: Websocket
        :return: None
        """

        # add websocket to sub loggers
        for sub_logger in self._sub_logger:
            sub_logger.add_websocket(websocket)

        # add websocket to action logger
        if websocket in self._websockets:
            return
        self._websockets.append(websocket)

    def remove_websocket(self, websocket: WebSocket) -> None:
        """
        Remove websocket from action logger.

        :param websocket: Websocket
        :return: None
        """

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

        # set parent logger
        if parent is None:
            parent = self.parent
        sub_logger.parent = parent

        # set log level
        if log_level is None:
            if parent is None:
                log_level = self.log_level
            else:
                log_level = parent.level
        sub_logger.setLevel(log_level)

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

        return ActionSubLoggerContext(action_logger=self,
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
        Exit action logger. Also remove all websockets and sub loggers.

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
