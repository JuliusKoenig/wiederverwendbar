import json
import logging
import asyncio
import string
import traceback
import warnings
from typing import Optional, Union, Any

from starlette.requests import Request
from starlette.websockets import WebSocket, WebSocketState
from starlette_admin.exceptions import ActionFailed

from wiederverwendbar.logger.context import LoggingContext

LOGGER = logging.getLogger(__name__)


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


class _SubLoggerCommand:
    def __init__(self, logger: logging.Logger, command: str, **values):
        record = logger.makeRecord(logger.name,
                                   logging.NOTSET,
                                   "",
                                   0,
                                   "",
                                   (),
                                   None,
                                   extra={"handling_command": {"command": command, "values": values}})
        logger.handle(record)


class StepCommand(_SubLoggerCommand):
    def __init__(self, logger: logging.Logger, step: int, steps: Optional[int] = None):
        super().__init__(logger, "step", step=step, steps=steps)


class NextStepCommand(_SubLoggerCommand):
    def __init__(self, logger: logging.Logger):
        super().__init__(logger, "next_step")

class IncreaseStepsCommand(_SubLoggerCommand):
    def __init__(self, logger: logging.Logger, steps: int):
        super().__init__(logger, "increase_steps", steps=steps)


class FinalizeCommand(_SubLoggerCommand):
    def __init__(self, logger: logging.Logger, success: bool, on_success_msg: Optional[str] = None, on_error_msg: Optional[str] = None):
        super().__init__(logger, "finalize", success=success, on_success_msg=on_success_msg, on_error_msg=on_error_msg)


class ExitCommand(_SubLoggerCommand):
    def __init__(self, logger: logging.Logger):
        super().__init__(logger, "exit")


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
        self._error_msg: Optional[str] = None

        # check if logger already exists
        if self.is_logger_exist(name=self.name):
            raise ValueError("ActionSubLogger already exists.")

        # create websocket handler
        websocket_handler = WebsocketHandler()
        self.addHandler(websocket_handler)

        # add logger to logger manager
        logging.root.manager.loggerDict[self.name] = self

        # start sub logger
        _SubLoggerCommand(logger=self, command="start")

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

    def handle(self, record) -> None:
        if self.exited:
            raise ValueError("ActionSubLogger already exited.")

        record.sub_logger = self.sub_logger_name

        if hasattr(record, "handling_command"):
            command_name: str = getattr(record, "handling_command")["command"]
            values: dict[str, Any] = getattr(record, "handling_command")["values"]
            del record.handling_command

            command = {"command": command_name}
            if command_name == "start":
                command["value"] = self.title
                record.command = command
                super().handle(record)
            elif command_name == "step":
                step = values["step"]
                steps = values["steps"]
                if steps is None:
                    return
                if steps < 0:
                    raise ValueError("Steps must be greater than 0.")
                if step >= steps:
                    step = steps
                calculated_progress = round(step / steps * 100)
                command["value"] = calculated_progress
                record.command = command
                super().handle(record)
                self._step = step
                self._steps = steps
            elif command_name == "next_step":
                self.step += 1
            elif command_name == "increase_steps":
                steps = values["steps"]
                if steps < 0:
                    raise ValueError("Steps must be greater than 0.")
                if self.steps is None:
                    self.steps = steps
                else:
                    self.steps += steps
            elif command_name == "finalize":
                success = values["success"]
                msg = values["on_success_msg"] if success else values["on_error_msg"]
                if success:
                    if self.steps is not None:
                        if self.step < self.steps:
                            self.step = self.steps
                if msg is not None:
                    if success:
                        self.log(logging.INFO, msg)
                    else:
                        self.log(logging.ERROR, msg)
                if not success:
                    self._error_msg = "Something went wrong." if values["on_error_msg"] is None else values["on_error_msg"]

                command["value"] = success
                record.command = command
                super().handle(record)
                self.exit()
            elif command_name == "exit":
                # remove websockets
                for websocket in self._websockets:
                    self.remove_websocket(websocket)

                # remove handler
                for handler in self.handlers:
                    self.removeHandler(handler)

                # remove logger from logger manager
                logging.root.manager.loggerDict.pop(self.name, None)
            else:
                raise ValueError("Invalid command.")
        else:
            super().handle(record)

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

        StepCommand(logger=self, step=self.step, steps=value)

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

        StepCommand(logger=self, step=value, steps=self.steps)

    def next_step(self) -> None:
        """
        Increase step by 1.

        :return: None
        """

        NextStepCommand(logger=self)

    def finalize(self,
                 success: bool = True,
                 on_success_msg: Optional[str] = None,
                 on_error_msg: Optional[str] = "Something went wrong.") -> None:
        """
        Finalize sub logger. Also send finalize command to websocket.

        :param success: If True, frontend will show success message. If False, frontend will show error message.
        :param on_success_msg: Message if success.
        :param on_error_msg: Message if error.
        :return: None
        """

        FinalizeCommand(logger=self, success=success, on_success_msg=on_success_msg, on_error_msg=on_error_msg)

    def exit(self) -> None:
        """
        Exit sub logger. Also remove websocket from sub logger.

        :return: None
        """

        ExitCommand(logger=self)

    @property
    def exited(self) -> bool:
        """
        Check if sub logger is exited.

        :return: True if exited, otherwise False.
        """

        return not self.is_logger_exist(name=self.name)

    @property
    def error_occurred(self) -> bool:
        """
        Check if error occurred.

        :return: True if error occurred, otherwise False.
        """

        return self._error_msg is not None

    @property
    def error_msg(self) -> Optional[str]:
        """
        Get error message.

        :return: Error message.
        """

        return self._error_msg


class ActionSubLoggerContext(LoggingContext):
    def __init__(self,
                 action_logger: "ActionLogger",
                 name: str,
                 title: Optional[str] = None,
                 log_level: int = logging.NOTSET,
                 parent: Optional[logging.Logger] = None,
                 formatter: Optional[logging.Formatter] = None,
                 steps: Optional[int] = None,
                 on_success_msg: Optional[str] = None,
                 on_error_msg: Optional[str] = "Something went wrong.",
                 show_errors: Optional[bool] = None,
                 halt_on_error: Optional[bool] = None,
                 use_context_logger_level: bool = True,
                 use_context_logger_level_on_not_set: Optional[bool] = None,
                 ignore_loggers_equal: Optional[list[str]] = None,
                 ignore_loggers_like: Optional[list[str]] = None,
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
        :param on_success_msg: Message of finalize message if success.
        :param on_error_msg: Message of finalize message if error.
        :param show_errors: Show errors in frontend. If None, action logger show_errors will be used.
        :param halt_on_error: Halt on error.
        :param use_context_logger_level: Use context logger level.
        :param use_context_logger_level_on_not_set: Use context logger level on not set.
        :param handle_origin_logger: Handle origin logger.
        """

        # create sub logger
        self.context_logger = action_logger.new_sub_logger(name=name, title=title, log_level=log_level, parent=parent, formatter=formatter, steps=steps)

        self.on_success_msg = on_success_msg
        self.on_error_msg = on_error_msg
        if show_errors is None:
            show_errors = action_logger.show_errors
        self.show_errors = show_errors
        if halt_on_error is None:
            halt_on_error = action_logger.halt_on_error
        self.halt_on_error = halt_on_error

        super().__init__(context_logger=self.context_logger,
                         use_context_logger_level=use_context_logger_level,
                         use_context_logger_level_on_not_set=use_context_logger_level_on_not_set,
                         ignore_loggers_equal=ignore_loggers_equal,
                         ignore_loggers_like=ignore_loggers_like,
                         handle_origin_logger=handle_origin_logger)

    def __enter__(self) -> "ActionSubLogger":
        super().__enter__()
        return self.context_logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)
        if self.context_logger.exited:
            return False
        else:
            if exc_type is None:
                self.context_logger.finalize(success=True, on_success_msg=self.on_success_msg, on_error_msg=self.on_error_msg)
            else:
                if exc_type is ActionFailed:
                    on_error_msg = exc_val.args[0]
                else:
                    on_error_msg = self.on_error_msg
                    if self.show_errors:
                        # get exception string
                        tb_str = traceback.format_exc()
                        if on_error_msg is None:
                            on_error_msg = tb_str
                        else:
                            on_error_msg = self.on_error_msg + "\n" + tb_str
                self.context_logger.finalize(success=False, on_success_msg=self.on_success_msg, on_error_msg=on_error_msg)
            return exc_type is None or not self.halt_on_error


class ActionLogger:
    _action_loggers: list["ActionLogger"] = []

    def __init__(self,
                 action_log_key_request_or_websocket: Union[str, Request],
                 log_level: int = logging.NOTSET,
                 parent: Optional[logging.Logger] = None,
                 formatter: Optional[logging.Formatter] = None,
                 show_errors: bool = True,
                 halt_on_error: bool = False,
                 wait_for_websocket: bool = True,
                 wait_for_websocket_timeout: int = 5):
        """
        Create new action logger.

        :param action_log_key_request_or_websocket: Action log key, request or websocket.
        :param log_level: Log level of action logger. If None, parent log level will be used. If parent is None, logging.INFO will be used.
        :param parent: Parent logger. If None, logger will be added to module logger.
        :param formatter: Formatter of action logger. If None, default formatter will be used.
        :param show_errors: Show errors in frontend.
        :param halt_on_error: Halt on error.
        :param wait_for_websocket: Wait for websocket to be connected.
        :param wait_for_websocket_timeout: Timeout in seconds.
        """

        self.action_log_key = self.get_action_key(action_log_key_request_or_websocket)
        self.show_errors = show_errors
        self.halt_on_error = halt_on_error

        # get parent logger
        if parent is None:
            parent = LOGGER
        self.parent = parent

        # set log level
        if log_level == logging.NOTSET:
            log_level = logging.INFO
            if self.parent is not None:
                if self.parent.level != logging.NOTSET:
                    log_level = self.parent.level
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
                LOGGER.debug(f"[{current_try}/{wait_for_websocket_timeout}] Waiting for websocket...")
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

        # check if error occurred in sub logger
        error_msg = ""
        for sub_logger in self._sub_logger:
            if sub_logger.error_occurred:
                error_msg += f"{sub_logger.title}: {sub_logger.error_msg}\n"
        if error_msg:
            raise ActionFailed(error_msg)

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
            LOGGER.debug(f"[{current_try}/{timeout}] Waiting for action logger...")
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
                       log_level: int = logging.NOTSET,
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
        if log_level == logging.NOTSET:
            log_level = self.log_level
            if parent is not None:
                if parent.level != logging.NOTSET:
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
                   log_level: int = logging.NOTSET,
                   parent: Optional[logging.Logger] = None,
                   formatter: Optional[logging.Formatter] = None,
                   steps: Optional[int] = None,
                   on_success_msg: Optional[str] = None,
                   on_error_msg: Optional[str] = "Something went wrong.",
                   show_errors: Optional[bool] = None,
                   halt_on_error: Optional[bool] = None,
                   use_context_logger_level: bool = True,
                   use_context_logger_level_on_not_set: Optional[bool] = None,
                   ignore_loggers_equal: Optional[list[str]] = None,
                   ignore_loggers_like: Optional[list[str]] = None,
                   handle_origin_logger: bool = True) -> ActionSubLoggerContext:

        """
        Sub logger context manager.

        :param name: Name of sub logger. Only a-z, A-Z, 0-9, - and _ are allowed.
        :param title: Title of sub logger. Visible in frontend.
        :param log_level: Log level of sub logger. If None, parent log level will be used. If parent is None, action logger log level will be used.
        :param parent: Parent logger. If None, action logger parent will be used.
        :param formatter: Formatter of sub logger. If None, action logger formatter will be used.
        :param steps: Steps of sub logger.
        :param on_success_msg: Message of finalize message if success.
        :param on_error_msg: Message of finalize message if error.
        :param show_errors: Show errors in frontend. If None, action logger show_errors will be used.
        :param halt_on_error: Halt on error.
        :param use_context_logger_level: Use context logger level.
        :param use_context_logger_level_on_not_set: Use context logger level on not set.
        :param ignore_loggers_equal: Ignore loggers equal to this list.
        :param ignore_loggers_like: Ignore loggers like this list.
        :param handle_origin_logger: Handle origin logger.
        :return:
        """

        return ActionSubLoggerContext(action_logger=self,
                                      name=name,
                                      title=title,
                                      log_level=log_level,
                                      parent=parent,
                                      formatter=formatter,
                                      steps=steps,
                                      on_success_msg=on_success_msg,
                                      on_error_msg=on_error_msg,
                                      show_errors=show_errors,
                                      halt_on_error=halt_on_error,
                                      use_context_logger_level=use_context_logger_level,
                                      use_context_logger_level_on_not_set=use_context_logger_level_on_not_set,
                                      ignore_loggers_equal=ignore_loggers_equal,
                                      ignore_loggers_like=ignore_loggers_like,
                                      handle_origin_logger=handle_origin_logger)

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
