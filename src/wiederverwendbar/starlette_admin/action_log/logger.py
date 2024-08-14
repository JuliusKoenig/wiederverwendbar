import inspect
import json
import logging
import asyncio
import string
import threading
import time
import traceback
from enum import Enum
from typing import Optional, Union, Any

from pydantic import BaseModel, ValidationError
from starlette.requests import Request
from starlette.websockets import WebSocket, WebSocketState
from starlette_admin.exceptions import ActionFailed

from wiederverwendbar.logger.context import LoggingContext

LOGGER = logging.getLogger(__name__)


class _SubLoggerCommand:
    def __init__(self, logger, allowed_logger_cls: list[type], command: str, **values):
        if not any([isinstance(logger, cls) for cls in allowed_logger_cls]):
            raise ValueError(f"Logger must be an instance of: {', '.join([cls.__name__ for cls in allowed_logger_cls])}.")
        self.logger = logger
        if isinstance(self.logger, ActionLogger):
            self.logger.send_command(ActionLoggerCommand(sub_logger="", command=command, value=values))
        else:
            self.logger.handle(self.logger.makeRecord(logger.name,
                                                      logging.NOTSET,
                                                      "",
                                                      0,
                                                      "",
                                                      (),
                                                      None,
                                                      extra={"handling_command": {"command": command, "values": values}}))


class StartCommand(_SubLoggerCommand):
    def __init__(self, logger: Union["ActionSubLogger", logging.Logger], formatter: Optional[logging.Formatter] = None, steps: Optional[int] = None):
        super().__init__(logger=logger, allowed_logger_cls=[ActionSubLogger, logging.Logger], command="start", formatter=formatter, steps=steps)


class StepCommand(_SubLoggerCommand):
    def __init__(self, logger: Union["ActionSubLogger", logging.Logger], step: int, steps: Optional[int] = None):
        super().__init__(logger=logger, allowed_logger_cls=[ActionSubLogger, logging.Logger], command="step", step=step, steps=steps)


class NextStepCommand(_SubLoggerCommand):
    def __init__(self, logger: Union["ActionSubLogger", logging.Logger]):
        super().__init__(logger=logger, allowed_logger_cls=[ActionSubLogger, logging.Logger], command="next_step")


class IncreaseStepsCommand(_SubLoggerCommand):
    def __init__(self, logger: Union["ActionSubLogger", logging.Logger], steps: int):
        super().__init__(logger=logger, allowed_logger_cls=[ActionSubLogger, logging.Logger], command="increase_steps", steps=steps)


class FormCommand(_SubLoggerCommand):
    def __init__(self, logger: Union["ActionLogger", "ActionSubLogger", logging.Logger], form: str, submit_btn_text: Optional[str] = None, abort_btn_text: Optional[str] = None):
        if submit_btn_text is None:
            submit_btn_text = "Submit"
        if abort_btn_text is None:
            abort_btn_text = "Abort"
        if not isinstance(logger, ActionLogger) and not isinstance(logger, ActionSubLogger):
            action_sub_loggers = ActionSubLoggerContext.get_from_stack(inspect.stack())
            action_sub_logger_context: Optional[ActionSubLoggerContext] = None
            for action_sub_logger_context in action_sub_loggers:
                if isinstance(action_sub_logger_context, ActionSubLoggerContext):
                    break
            if action_sub_logger_context is None:
                raise ValueError(f"No action logger found. Did you use the {ActionSubLoggerContext.__name__} context manager?")
            logger = action_sub_logger_context.context_logger

        super().__init__(logger=logger, allowed_logger_cls=[ActionLogger, ActionSubLogger, logging.Logger], command="form", form=form, submit_btn_text=submit_btn_text,
                         abort_btn_text=abort_btn_text)

    def __call__(self, timeout: int = -1) -> Union[bool, dict[str, Any]]:
        if isinstance(self.logger, ActionLogger) or isinstance(self.logger, ActionSubLogger):
            return asyncio.run(self.logger.form_data(timeout=timeout))
        else:
            raise ValueError("Logger must be an instance of ActionLogger or ActionSubLogger.")


class YesNoCommand(FormCommand):
    def __init__(self, logger: Union["ActionLogger", "ActionSubLogger", logging.Logger], text: str, submit_btn_text: Optional[str] = None, abort_btn_text: Optional[str] = None):
        form = f"""<form>
            <div class="mt-3">
                <p>{text}</p>
            </div>
            </form>"""
        if submit_btn_text is None:
            submit_btn_text = "Yes"
        if abort_btn_text is None:
            abort_btn_text = "No"
        super().__init__(logger=logger, form=form, submit_btn_text=submit_btn_text, abort_btn_text=abort_btn_text)


class FinalizeCommand(_SubLoggerCommand):
    def __init__(self, logger: Union["ActionSubLogger", logging.Logger], success: bool, on_success_msg: Optional[str] = None, on_error_msg: Optional[str] = None):
        super().__init__(logger=logger, allowed_logger_cls=[ActionSubLogger, logging.Logger], command="finalize", success=success, on_success_msg=on_success_msg,
                         on_error_msg=on_error_msg)


class ExitCommand(_SubLoggerCommand):
    def __init__(self, logger: Union["ActionSubLogger", logging.Logger]):
        super().__init__(logger=logger, allowed_logger_cls=[ActionSubLogger, logging.Logger], command="exit")


class ActionLoggerCommand(BaseModel):
    class Command(str, Enum):
        EXIT = "exit"
        FINALIZE = "finalize"
        FORM = "form"
        INCREASE_STEPS = "increase_steps"
        LOG = "log"
        NEXT_STEP = "next_step"
        START = "start"
        STEP = "step"

    sub_logger: str
    command: Command
    value: Union[str, int, dict[str, Any]]


class ActionLoggerResponse(BaseModel):
    class Command(str, Enum):
        FORM = "form"

    sub_logger: str
    command: Command
    value: dict[str, Any]


class WebsocketHandler(logging.Handler):
    def __init__(self, sub_logger: "ActionSubLogger"):
        """
        Create new websocket handler.

        :return: None
        """

        super().__init__()

        self.sub_logger: ActionSubLogger = sub_logger

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit log record.

        :param record: Log record
        :return: None
        """

        # get extra
        sub_logger_name = getattr(record, "sub_logger")
        command: dict[str, Any] = getattr(record, "command", None)

        command_dict = {"sub_logger": sub_logger_name}

        # check if record is command
        if command is not None:
            command_dict.update(command)
        else:
            msg = self.format(record)
            command_dict.update({"command": "log", "value": msg})

        # send command to ActionLogger
        self.sub_logger.action_logger.send_command(command_dict)


class ActionSubLogger(logging.Logger):
    def __init__(self,
                 action_logger: "ActionLogger",
                 name: str,
                 title: Optional[str] = None,
                 websocket_handler_cls: Optional[type[WebsocketHandler]] = None):
        """
        Create new action sub logger.

        :param action_logger: Action logger
        :param name: Name of sub logger. Only a-z, A-Z, 0-9, - and _ are allowed.
        :param title: Title of sub logger. Visible in frontend.
        :param websocket_handler_cls: Websocket handler class.
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
        self._started: bool = False
        self._steps: Optional[int] = None
        self._step: int = 0
        self._error_msg: Optional[str] = None
        self._response_obj: Union[None, bool, ActionLoggerResponse] = None

        # check if logger already exists
        if self.is_logger_exist(name=self.name):
            raise ValueError("ActionSubLogger already exists.")

        # set websocket_handler_cls
        self.websocket_handler_cls: type[WebsocketHandler] = websocket_handler_cls or WebsocketHandler

    def __del__(self):
        if not self.exited:
            self.exit()

    @property
    def action_logger(self) -> "ActionLogger":
        """
        Get action logger.

        :return: Action logger.
        """

        return self._action_logger

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
        record.sub_logger = self.sub_logger_name

        if hasattr(record, "handling_command"):
            command_name: str = getattr(record, "handling_command")["command"]
            values: dict[str, Any] = getattr(record, "handling_command")["values"]
            del record.handling_command

            command = {"command": command_name}
            if command_name == "start":
                if self.started:
                    raise ValueError("ActionSubLogger already started.")
                if not self.exited:
                    raise ValueError("ActionSubLogger not exited.")

                # add websocket handler
                self.addHandler(self.websocket_handler_cls(sub_logger=self))

                # set formatter
                formatter = values["formatter"]
                if formatter is None:
                    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d - %H:%M:%S")
                for handler in self.handlers:
                    handler.setFormatter(formatter)

                # add logger to logger manager
                logging.root.manager.loggerDict[self.name] = self

                command["value"] = self.title
                record.command = command
                super().handle(record)
                self._started = True

                # set steps
                steps = values["steps"]
                if steps is not None:
                    self.steps = steps
            elif command_name == "step":
                if not self.started:
                    raise ValueError("ActionSubLogger not started.")
                if self.exited:
                    raise ValueError("ActionSubLogger already exited.")
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
                if not self.started:
                    raise ValueError("ActionSubLogger not started.")
                if self.exited:
                    raise ValueError("ActionSubLogger already exited.")
                self.step += 1
            elif command_name == "increase_steps":
                if not self.started:
                    raise ValueError("ActionSubLogger not started.")
                if self.exited:
                    raise ValueError("ActionSubLogger already exited.")
                steps = values["steps"]
                if steps < 0:
                    raise ValueError("Steps must be greater than 0.")
                if self.steps is None:
                    self.steps = steps
                else:
                    self.steps += steps
            elif command_name == "form":
                if not self.started:
                    raise ValueError("ActionSubLogger not started.")
                if self.exited:
                    raise ValueError("ActionSubLogger already exited.")
                submit_btn_text = values["submit_btn_text"]
                abort_btn_text = values["abort_btn_text"]
                form = values["form"]
                command["value"] = {"submit_btn_text": submit_btn_text, "abort_btn_text": abort_btn_text, "form": form}
                record.command = command
                super().handle(record)
            elif command_name == "finalize":
                if not self.started:
                    raise ValueError("ActionSubLogger not started.")
                if self.exited:
                    raise ValueError("ActionSubLogger already exited.")
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
                if not self.started:
                    raise ValueError("ActionSubLogger not started.")
                if self.exited:
                    raise ValueError("ActionSubLogger already exited.")

                # remove handler
                for handler in self.handlers:
                    self.removeHandler(handler)

                # remove logger from logger manager
                logging.root.manager.loggerDict.pop(self.name, None)
            else:
                raise ValueError("Invalid command.")
        else:
            super().handle(record)

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

    def start(self, formatter: Optional[logging.Formatter] = None, steps: Optional[int] = None) -> None:
        """
        Start sub logger.

        :param formatter: Formatter
        :param steps: Steps
        :return: None
        """

        StartCommand(logger=self, formatter=formatter, steps=steps)

    @property
    def started(self) -> bool:
        """
        Check if sub logger is started.

        :return: True if started, otherwise False.
        """

        return self._started

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

    def form(self, form: str, submit_btn_text: Optional[str] = None, abort_btn_text: Optional[str] = None) -> FormCommand:
        """
        Send form to frontend.

        :param form: Form HTML.
        :param submit_btn_text: Text of submit button.
        :param abort_btn_text: Text of cancel button.
        :return: Form data.
        """

        return FormCommand(logger=self, form=form, submit_btn_text=submit_btn_text, abort_btn_text=abort_btn_text)

    def yes_no(self, text: str, submit_btn_text: Optional[str] = None, abort_btn_text: Optional[str] = None) -> YesNoCommand:
        """
        Send yes/no form to frontend.

        :param text: Text of yes/no form.
        :param submit_btn_text: Text of submit button.
        :param abort_btn_text: Text of cancel button.
        :return: Form data.
        """

        return YesNoCommand(logger=self, text=text, submit_btn_text=submit_btn_text, abort_btn_text=abort_btn_text)

    async def await_response(self, timeout: int = -1) -> Union[bool, ActionLoggerResponse]:
        """
        Fetch response from frontend.

        :param timeout: Timeout in seconds. If -1, no timeout will be set.
        :return: Form data.
        """

        return await self.action_logger._await_response(logger=self, timeout=timeout)

    async def form_data(self, timeout: int = -1) -> Union[bool, dict[str, Any]]:
        """
        Fetch form data from frontend.

        :param timeout: Timeout in seconds. If -1, no timeout will be set.
        :return: Form data.
        """

        return await self.action_logger._form_data(logger=self, timeout=timeout)

    @property
    def awaiting_response(self) -> bool:
        """
        Check if sub logger is awaiting response.

        :return: True if awaiting response, otherwise False.
        """

        return self.action_logger._awaiting_response(logger=self)

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
                 handle_origin_logger: bool = True,
                 action_sub_logger_cls: Optional[type[ActionSubLogger]] = None,
                 websocket_handler_cls: Optional[type[WebsocketHandler]] = None):
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
        :param ignore_loggers_equal: Ignore loggers equal.
        :param ignore_loggers_like: Ignore loggers like.
        :param handle_origin_logger: Handle origin logger.
        :param action_sub_logger_cls: Action sub logger class.
        :param websocket_handler_cls: Websocket handler class.
        """

        self._action_logger = action_logger
        self._formatter = formatter or self._action_logger.formatter
        self._steps = steps

        # create sub logger
        self.context_logger = self._action_logger.new_sub_logger(name=name,
                                                                 title=title,
                                                                 log_level=log_level,
                                                                 parent=parent,
                                                                 action_sub_logger_cls=action_sub_logger_cls,
                                                                 websocket_handler_cls=websocket_handler_cls)

        self.on_success_msg = on_success_msg
        self.on_error_msg = on_error_msg
        self.show_errors = show_errors or self._action_logger.show_errors
        self.halt_on_error = halt_on_error or action_logger.halt_on_error

        super().__init__(context_logger=self.context_logger,
                         use_context_logger_level=use_context_logger_level,
                         use_context_logger_level_on_not_set=use_context_logger_level_on_not_set,
                         ignore_loggers_equal=ignore_loggers_equal,
                         ignore_loggers_like=ignore_loggers_like,
                         handle_origin_logger=handle_origin_logger)

    def __enter__(self) -> "ActionSubLogger":
        super().__enter__()
        self.context_logger.start(formatter=self._formatter, steps=self._steps)

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

        self.lock = threading.Lock()
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
        self.formatter = formatter

        self._global_buffer: list[str] = []  # global websocket buffer
        self._websockets: dict[WebSocket, list[str]] = {}  # websocket, websocket_buffer
        self._sub_logger: list[ActionSubLogger] = []
        self._response_obj: Union[None, bool, ActionLoggerResponse] = None

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
        Add websocket to action logger. All global buffer will be sent to websocket buffer. After that, all buffered records will be sent to websocket.

        :param websocket: Websocket
        :return: None
        """

        with self.lock:
            # add websocket to action logger
            if websocket in self._websockets.keys():
                raise ValueError("Websocket already exists.")

            # create buffer for websocket
            self._websockets[websocket] = []

            # push all global buffer to websocket buffer
            for record in self._global_buffer:
                self._websockets[websocket].append(record)

            # send all buffered records to websocket
            self._send_all()

    def remove_websocket(self, websocket: WebSocket) -> None:
        """
        Remove websocket from action logger. All buffered records will be sent to websocket.

        :param websocket: Websocket
        :return: None
        """

        with self.lock:
            # remove websocket from action logger
            if websocket not in self._websockets.keys():
                raise ValueError("Websocket not exists.")

            # send all buffered records to websocket
            self._send_all()

            # remove websocket from websocket buffer
            del self._websockets[websocket]

    def new_sub_logger(self,
                       name: str,
                       title: Optional[str] = None,
                       log_level: int = logging.NOTSET,
                       parent: Optional[logging.Logger] = None,
                       action_sub_logger_cls: Optional[type[ActionSubLogger]] = None,
                       websocket_handler_cls: Optional[type[WebsocketHandler]] = None) -> ActionSubLogger:
        """
        Create new sub logger.

        :param name: Name of sub logger. Only a-z, A-Z, 0-9, - and _ are allowed.
        :param title: Title of sub logger. Visible in frontend.
        :param log_level: Log level of sub logger. If None, parent log level will be used. If parent is None, action logger log level will be used.
        :param parent: Parent logger. If None, action logger parent will be used.
        :param action_sub_logger_cls: Action sub logger class.
        :param websocket_handler_cls: Websocket handler class.
        :return: Sub logger.
        """

        try:
            self.get_sub_logger(sub_logger_name=name)
        except ValueError:
            pass

        with self.lock:
            # create sub logger
            action_sub_logger_cls = action_sub_logger_cls or ActionSubLogger
            sub_logger = action_sub_logger_cls(action_logger=self, name=name, title=title, websocket_handler_cls=websocket_handler_cls)

            # set parent logger
            parent = parent or self.parent
            sub_logger.parent = parent

            # set log level
            if log_level == logging.NOTSET:
                log_level = self.log_level
                if parent is not None:
                    if parent.level != logging.NOTSET:
                        log_level = parent.level
            sub_logger.setLevel(log_level)

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
                   handle_origin_logger: bool = True,
                   action_sub_logger_cls: Optional[type[ActionSubLogger]] = None,
                   websocket_handler_cls: Optional[type[WebsocketHandler]] = None) -> ActionSubLoggerContext:

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
        :param action_sub_logger_cls: Action sub logger class.
        :param websocket_handler_cls: Websocket handler class.
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
                                      handle_origin_logger=handle_origin_logger,
                                      action_sub_logger_cls=action_sub_logger_cls,
                                      websocket_handler_cls=websocket_handler_cls)

    def form(self, form: str, submit_btn_text: Optional[str] = None, abort_btn_text: Optional[str] = None) -> FormCommand:
        """
        Send form to frontend.

        :param form: Form HTML.
        :param submit_btn_text: Text of submit button.
        :param abort_btn_text: Text of cancel button.
        :return: Form data.
        """

        return FormCommand(logger=self, form=form, submit_btn_text=submit_btn_text, abort_btn_text=abort_btn_text)

    def yes_no(self, text: str, submit_btn_text: Optional[str] = None, abort_btn_text: Optional[str] = None) -> YesNoCommand:
        """
        Send yes/no form to frontend.

        :param text: Text of yes/no form.
        :param submit_btn_text: Text of submit button.
        :param abort_btn_text: Text of cancel button.
        :return: Form data.
        """

        return YesNoCommand(logger=self, text=text, submit_btn_text=submit_btn_text, abort_btn_text=abort_btn_text)

    @classmethod
    async def _await_response(cls, logger: Union["ActionLogger", ActionSubLogger], timeout: int = -1) -> Union[bool, ActionLoggerResponse]:
        if not isinstance(logger, ActionLogger) and not isinstance(logger, ActionSubLogger):
            raise ValueError("Invalid logger.")

        if not logger.awaiting_response:
            raise ValueError("Logger is not awaiting form data.")

        start_wait = time.perf_counter()
        while logger.awaiting_response:
            if timeout != -1:
                if time.perf_counter() - start_wait > timeout:
                    return False
            await asyncio.sleep(0.001)

        # get response object
        response_obj = getattr(logger, "_response_obj")
        setattr(logger, "_response_obj", None)
        logger_name = getattr(logger, "sub_logger_name", "")

        # check is response object is for this logger
        if not response_obj.sub_logger == logger_name:
            raise ValueError("The response object is not for this logger.")

        return response_obj

    async def await_response(self, timeout: int = -1) -> Union[bool, ActionLoggerResponse]:
        """
        Fetch response from frontend.

        :param timeout: Timeout in seconds. If -1, no timeout will be set.
        :return: Form data.
        """

        return await self._await_response(logger=self, timeout=timeout)

    @classmethod
    async def _form_data(cls, logger: Union["ActionLogger", ActionSubLogger], timeout: int = -1) -> Union[bool, dict[str, Any]]:
        response_obj = await logger.await_response(timeout=timeout)
        if response_obj is False:
            return False

        # check if response object is form
        if response_obj.command != ActionLoggerResponse.Command.FORM:
            raise ValueError("Response object is not form.")

        # check "result" key is bool
        if not isinstance(response_obj.value["result"], bool):
            raise ValueError("Invalid result.")

        if len(response_obj.value["form_data"]) == 0 or not response_obj.value["result"]:
            return response_obj.value["result"]

        return response_obj.value["form_data"]

    async def form_data(self, timeout: int = -1) -> Union[bool, dict[str, Any]]:
        """
        Fetch form data from frontend.

        :param timeout: Timeout in seconds. If -1, no timeout will be set.
        :return: Form data.
        """

        return await self._form_data(logger=self, timeout=timeout)

    @classmethod
    def _awaiting_response(cls, logger: Union["ActionLogger", ActionSubLogger]) -> bool:
        if not isinstance(logger, ActionLogger) and not isinstance(logger, ActionSubLogger):
            raise ValueError("Invalid logger.")

        # get response object
        response_obj = getattr(logger, "_response_obj")

        if response_obj is None:
            return False
        elif type(response_obj) == bool:
            return True
        elif isinstance(response_obj, ActionLoggerResponse):
            return False
        else:
            raise ValueError("Invalid response object.")

    @property
    def awaiting_response(self) -> bool:
        """
        Check if logger is awaiting response.

        :return: True if awaiting response, otherwise False.
        """

        return self._awaiting_response(logger=self)

    def exit(self):
        """
        Exit action logger. Also remove all websockets and sub loggers.

        :return: None
        """

        if self.exited:
            raise ValueError("ActionLogger already exited.")

        # remove websockets
        for websocket in list(self._websockets.keys()):
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

    @classmethod
    def parse_response_obj(cls, data: str) -> Union[None, ActionLoggerResponse]:
        """
        Parse response object.

        :param data: Data
        :return: Response object
        """

        # parse to dict
        try:
            response_obj_dict = json.loads(data)
        except json.JSONDecodeError as e:
            LOGGER.error(f"JSONDecodeError while parsing response object: {e}")
            return None

        # create response object
        try:
            response_obj = ActionLoggerResponse(**response_obj_dict)
        except ValidationError as e:
            LOGGER.error(f"ValidationError while parsing response object: {e}")
            return None

        return response_obj

    def _send(self, websocket: WebSocket, command_json: str) -> None:
        """
        Send command to websocket.

        :param websocket: Websocket
        :param command_json: Command JSON
        :return: None
        """

        # check websocket is connected
        if websocket.client_state != WebSocketState.CONNECTED:
            raise ValueError("Websocket is not connected.")

        # send command message
        asyncio.run(websocket.send_text(command_json))

    def _send_all(self) -> None:
        """
        Send all buffered commands to all websockets.

        :return: None
        """

        # send buffered records
        for websocket in self._websockets.keys():
            while self._websockets[websocket]:
                buffered_command = self._websockets[websocket].pop(0)
                self._send(websocket, buffered_command)

    def send_command(self, command: Union[dict[str, Any], ActionLoggerCommand]) -> None:
        """
        Send command to all websockets.

        :param command: Command. If dict, it will be converted to ActionLoggerCommand.
        :return: None
        """

        # validate command
        if type(command) is dict:
            command = ActionLoggerCommand(**command)
        if not isinstance(command, ActionLoggerCommand):
            raise ValueError("Invalid command.")

        # convert command to json
        command_json = command.model_dump_json()

        with self.lock:
            # check if action logger or any sub logger is awaiting response
            if self.awaiting_response:
                raise ValueError("ActionLogger is awaiting response.")
            for sub_logger in self._sub_logger:
                if sub_logger.awaiting_response:
                    raise ValueError("Sub logger is awaiting response.")

            # get action logger or sub logger
            if command.sub_logger == "":
                logger = self
            else:
                logger = self.get_sub_logger(sub_logger_name=command.sub_logger)

            # set _response_obj to True if command is available in ActionLoggerResponse.Command
            try:
                ActionLoggerResponse.Command(command.command.value)
                logger._response_obj = True
            except ValueError:
                logger._response_obj = None

            # add command to global buffer
            self._global_buffer.append(command_json)

            # add command to websocket buffer
            for websocket in self._websockets.keys():
                self._websockets[websocket].append(command_json)

            # send all
            self._send_all()

    def send_response_to_logger(self, response_obj: ActionLoggerResponse) -> None:
        """
        Send response object to sub logger.

        :param response_obj: Response object
        :return: None
        """

        with self.lock:
            if response_obj.sub_logger == "":
                logger = self
            else:
                # get sub logger
                logger = self.get_sub_logger(sub_logger_name=response_obj.sub_logger)

            # check if sub logger is awaiting response
            if not logger.awaiting_response:
                raise ValueError("Logger is not awaiting response.")

            # set response object
            setattr(logger, "_response_obj", response_obj)
