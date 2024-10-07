import asyncio
import inspect
import json
import logging
import string
import time
import traceback
from enum import Enum
from pathlib import Path
from threading import Thread
from typing import Optional, Union, Any
from socket import timeout as socket_timeout
from warnings import warn

from pydantic import BaseModel, ValidationError
from starlette.requests import Request
from starlette.websockets import WebSocket
from starlette_admin.exceptions import ActionFailed
from kombu import Connection, Exchange, Queue, Message, Producer

from wiederverwendbar.logger.context import LoggingContext
from wiederverwendbar.starlette_admin.action_log.settings import ActionLogAdminSettings

LOGGER = logging.getLogger(__name__)
KOMBU_EXCHANGE_NAME = "action_log"


class _SubLoggerCommand:
    def __init__(self,
                 logger, allowed_logger_cls: list[type],
                 command: str,
                 **values):
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
    def __init__(self,
                 logger: Union["ActionSubLogger", logging.Logger],
                 steps: Optional[int] = None):
        super().__init__(logger=logger,
                         allowed_logger_cls=[ActionSubLogger, logging.Logger],
                         command="start",
                         steps=steps)


class StepCommand(_SubLoggerCommand):
    def __init__(self,
                 logger: Union["ActionSubLogger", logging.Logger],
                 step: int,
                 steps: Optional[int] = None):
        super().__init__(logger=logger,
                         allowed_logger_cls=[ActionSubLogger, logging.Logger],
                         command="step",
                         step=step,
                         steps=steps)


class NextStepCommand(_SubLoggerCommand):
    def __init__(self,
                 logger: Union["ActionSubLogger", logging.Logger],
                 steps: int = 1):
        super().__init__(logger=logger,
                         allowed_logger_cls=[ActionSubLogger, logging.Logger],
                         command="next_step",
                         steps=steps)


class IncreaseStepsCommand(_SubLoggerCommand):
    def __init__(self,
                 logger: Union["ActionSubLogger", logging.Logger],
                 steps: int):
        super().__init__(logger=logger,
                         allowed_logger_cls=[ActionSubLogger, logging.Logger],
                         command="increase_steps",
                         steps=steps)


class FormCommand(_SubLoggerCommand):
    def __init__(self,
                 logger: Union["ActionLogger", "ActionSubLogger", logging.Logger],
                 form: str,
                 submit_btn_text: Optional[str] = None,
                 abort_btn_text: Optional[str] = None,
                 default_values: Union[None, bool, dict[str, Any]] = None):
        if submit_btn_text is None:
            submit_btn_text = "OK"
        try:
            self.get_logger(logger)
        except ValueError:
            if default_values is None:
                raise ValueError(f"No action logger found. Did you use the {ActionSubLoggerContext.__name__} context manager? If not, you have to provide default values.")
        self.default_values: Union[None, bool, dict[str, Any]] = default_values

        super().__init__(logger=logger,
                         allowed_logger_cls=[ActionLogger, ActionSubLogger, logging.Logger],
                         command="form",
                         form=form,
                         submit_btn_text=submit_btn_text,
                         abort_btn_text=abort_btn_text)

    def __call__(self, timeout: Optional[float] = None) -> Union[bool, dict[str, Any]]:
        if isinstance(self.logger, ActionLogger) or isinstance(self.logger, ActionSubLogger):
            return asyncio.run(self.logger.form_data(timeout=timeout))
        elif isinstance(self.logger, logging.Logger):
            if self.default_values is None:
                raise ValueError("No default values provided.")
            return self.default_values
        else:
            raise ValueError("Logger must be an instance of ActionLogger, ActionSubLogger or logging.Logger.")

    @classmethod
    def get_logger(cls, logger: Union["ActionLogger", "ActionSubLogger", logging.Logger]) -> Union["ActionLogger", "ActionSubLogger"]:
        if isinstance(logger, ActionLogger) or isinstance(logger, ActionSubLogger):
            return logger
        action_sub_loggers = ActionSubLoggerContext.get_from_stack(inspect.stack())
        action_sub_logger_context: Optional[ActionSubLoggerContext] = None
        for action_sub_logger_context in action_sub_loggers:
            if isinstance(action_sub_logger_context, ActionSubLoggerContext):
                break
        if action_sub_logger_context is None:
            raise ValueError(f"No action logger found. Did you use the {ActionSubLoggerContext.__name__} context manager? If not, you have to provide default values.")
        return action_sub_logger_context.context_logger


class ConfirmCommand(FormCommand):
    def __init__(self,
                 logger: Union["ActionLogger", "ActionSubLogger", logging.Logger],
                 text: str,
                 submit_btn_text: Optional[str] = None,
                 form: Optional[str] = None):
        if form is None:
            form = f"""<form>
            <div class="mt-3">
                <p>{text}</p>
            </div>
            </form>"""
        super().__init__(logger=logger,
                         form=form,
                         submit_btn_text=submit_btn_text,
                         default_values=True)

    def __call__(self, timeout: Optional[float] = None) -> None:
        super().__call__(timeout=timeout)


class DownloadCommand(ConfirmCommand):
    def __init__(self,
                 logger: Union["ActionLogger", "ActionSubLogger", logging.Logger],
                 file_path: Union[str, Path],
                 text: str,
                 icon: Optional[str] = None,
                 submit_btn_text: Optional[str] = None,
                 form: Optional[str] = None):
        # check if file exists
        if type(file_path) is str:
            file_path = Path(file_path)
        if not file_path.is_file():
            raise ValueError(f"File '{file_path}' does not exist.")

        # get logger
        logger = self.get_logger(logger)
        if isinstance(logger, ActionLogger):
            action_logger: ActionLogger = logger

        else:
            action_logger: ActionLogger = logger.action_logger
        action_log_download_url = f"{action_logger.admin.base_url}/action_log/download/{action_logger.action_log_key}"

        # get producer, exchange and download_queue
        producer: Producer = getattr(action_logger, "_producer")
        exchange: Exchange = getattr(action_logger, "_exchange")
        download_queue: Queue = getattr(action_logger, "_download_queue")

        # send download command
        producer.publish({"file_path": str(file_path)}, exchange=exchange, routing_key=download_queue.name)

        if icon is None:
            icon = "fa fa-download"
        if form is None:
            form = f"""<form>
                <a href="{action_log_download_url}" download>
                <p>{text}</p>
            </form>"""

        super().__init__(logger=logger,
                         text=text,
                         submit_btn_text=submit_btn_text,
                         form=form)

    def __call__(self, timeout: Optional[float] = None) -> None:
        super().__call__(timeout=timeout)


class YesNoCommand(FormCommand):
    def __init__(self,
                 logger: Union["ActionLogger", "ActionSubLogger", logging.Logger],
                 text: str, submit_btn_text: Optional[str] = None,
                 abort_btn_text: Optional[str] = None,
                 default_value: Optional[bool] = None,
                 form: Optional[str] = None):
        if form is None:
            form = f"""<form>
            <div class="mt-3">
                <p>{text}</p>
            </div>
            </form>"""
        if submit_btn_text is None:
            submit_btn_text = "Yes"
        if abort_btn_text is None:
            abort_btn_text = "No"
        super().__init__(logger=logger,
                         form=form,
                         submit_btn_text=submit_btn_text,
                         abort_btn_text=abort_btn_text,
                         default_values=default_value)

    def __call__(self, timeout: Optional[float] = None) -> bool:
        result = super().__call__(timeout=timeout)
        if type(result) is not bool:
            raise ValueError("Invalid response.")
        return result


class FinalizeCommand(_SubLoggerCommand):
    def __init__(self,
                 logger: Union["ActionSubLogger", logging.Logger],
                 success: bool,
                 on_success_msg: Optional[str] = None,
                 on_error_msg: Optional[str] = None,
                 on_error_msg_simple: Optional[str] = None,
                 end_steps: Optional[bool] = None):
        super().__init__(logger=logger,
                         allowed_logger_cls=[ActionSubLogger, logging.Logger],
                         command="finalize",
                         success=success,
                         on_success_msg=on_success_msg,
                         on_error_msg=on_error_msg,
                         on_error_msg_simple=on_error_msg_simple,
                         end_steps=end_steps)


class ExitCommand(_SubLoggerCommand):
    def __init__(self,
                 logger: Union["ActionSubLogger", logging.Logger]):
        super().__init__(logger=logger,
                         allowed_logger_cls=[ActionSubLogger, logging.Logger],
                         command="exit")


class ActionLoggerCommand(BaseModel):
    class Command(str, Enum):
        START = "start"
        INCREASE_STEPS = "increase_steps"
        STEP = "step"
        NEXT_STEP = "next_step"
        LOG = "log"
        FORM = "form"
        FINALIZE = "finalize"
        EXIT = "exit"

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
                 parent: Optional[logging.Logger] = None,
                 log_level: Optional[ActionLogAdminSettings.LogLevels] = None,
                 formatter: Optional[logging.Formatter] = None,
                 websocket_handler_cls: Optional[type[WebsocketHandler]] = None):
        """
        Create new action sub logger.

        :param action_logger: Action logger
        :param name: Name of sub logger. Only a-z, A-Z, 0-9, - and _ are allowed.
        :param title: Title of sub logger. Visible in frontend.
        :param websocket_handler_cls: Websocket handler class.
        """

        # validate name
        if not name:
            raise ValueError("Name must not be empty.")
        for char in name:
            if char not in string.ascii_letters + string.digits + "-" + "_":
                raise ValueError("Invalid character in name. Only a-z, A-Z, 0-9, - and _ are allowed.")

        super().__init__(name=action_logger.action_log_key + "." + name)

        self._action_logger = action_logger

        # set title
        if title is None:
            title = name
        self._title = title

        # set parent
        if parent is None:
            parent = self._action_logger.parent
        self.parent = parent

        # set log level
        if log_level is None:
            log_level = self._action_logger.log_level
        self.setLevel(log_level.value)

        # set formatter
        if formatter is None:
            formatter = self._action_logger.formatter
        self._formatter = formatter

        # initialize variables
        self._started: bool = False
        self._steps: Optional[int] = None
        self._step: int = 0
        self._error_occurred: bool = False
        self._finalize_msg: Optional[str] = None
        self._finalize_msg_simple: Optional[str] = None
        self._response_obj: Union[None, bool, ActionLoggerResponse] = None

        # check if logger already exists
        if self.is_logger_exist(name=self.name):
            raise ValueError("ActionSubLogger already exists.")

        # set websocket_handler_cls
        self.websocket_handler_cls: type[WebsocketHandler] = websocket_handler_cls or self._action_logger.websocket_handler_cls

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
                for handler in self.handlers:
                    handler.setFormatter(self._formatter)

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
                steps = values["steps"]
                self.step += steps
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
                end_steps = values["end_steps"]
                self._error_occurred = not success
                self._finalize_msg = values["on_success_msg"] if success else values["on_error_msg"]
                self._finalize_msg_simple = values["on_error_msg_simple"]
                contexts = ActionSubLoggerContext.get_from_stack(inspect.stack())
                current_context: Union[None, ActionSubLoggerContext, LoggingContext] = None
                if len(contexts) > 0:
                    current_context = contexts[-1]
                if not isinstance(current_context, ActionSubLoggerContext) and current_context is not None:
                    raise ValueError("Wrong context.")
                if end_steps is None:
                    if current_context is not None:
                        end_steps = current_context.end_steps

                if success:
                    if end_steps is None:
                        end_steps = True
                    if self._finalize_msg is None:
                        if current_context is not None:
                            self._finalize_msg = current_context.on_success_msg
                    if self._finalize_msg is None:
                        self._finalize_msg = "Success."
                    self.log(logging.INFO, self.finalize_msg)

                else:
                    if end_steps is None:
                        end_steps = False
                    if self._finalize_msg is None:
                        if current_context is not None:
                            self._finalize_msg = current_context.on_error_msg
                    if self._finalize_msg is None:
                        self._finalize_msg = "Something went wrong."
                    self.log(logging.ERROR, self.finalize_msg)

                if self.steps is not None and end_steps:
                    if self.step < self.steps:
                        self.step = self.steps

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

    def start(self, steps: Optional[int] = None) -> None:
        """
        Start sub logger.

        :param steps: Steps
        :return: None
        """

        StartCommand(logger=self, steps=steps)

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

    def confirm(self, text: str, submit_btn_text: Optional[str] = None, form: Optional[str] = None) -> ConfirmCommand:
        """
        Send confirm form to frontend.

        :param text: Text of confirm form.
        :param submit_btn_text: Text of submit button.
        :param form: Form HTML.
        :return: Form data.
        """

        return ConfirmCommand(logger=self, text=text, submit_btn_text=submit_btn_text, form=form)

    def download(self, file_path: Union[str, Path], text: str, icon: Optional[str] = None, submit_btn_text: Optional[str] = None,
                 form: Optional[str] = None) -> DownloadCommand:
        """
        Send download form to frontend.

        :param file_path: File path
        :param text: Text of download form.
        :param icon: Icon of download form.
        :param submit_btn_text: Text of submit button.
        :param form: Form HTML.
        :return: Form data.
        """

        return DownloadCommand(logger=self, file_path=file_path, text=text, icon=icon, submit_btn_text=submit_btn_text, form=form)

    def yes_no(self, text: str, submit_btn_text: Optional[str] = None, abort_btn_text: Optional[str] = None, form: Optional[str] = None) -> YesNoCommand:
        """
        Send yes/no form to frontend.

        :param text: Text of yes/no form.
        :param submit_btn_text: Text of submit button.
        :param abort_btn_text: Text of cancel button.
        :param form: Form HTML.
        :return: Form data.
        """

        return YesNoCommand(logger=self, text=text, submit_btn_text=submit_btn_text, abort_btn_text=abort_btn_text, form=form)

    async def await_response(self, timeout: Optional[float] = None) -> Union[bool, ActionLoggerResponse]:
        """
        Fetch response from frontend.

        :param timeout: Timeout in seconds.
        :return: Form data.
        """

        return await self.action_logger._await_response(logger=self, timeout=timeout)

    async def form_data(self, timeout: Optional[float] = None) -> Union[bool, dict[str, Any]]:
        """
        Fetch form data from frontend.

        :param timeout: Timeout in seconds.
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
                 on_error_msg: Optional[str] = None,
                 on_error_msg_simple: Optional[str] = None,
                 end_steps: Optional[bool] = None) -> None:
        """
        Finalize sub logger. Also send finalize command to websocket.

        :param success: If True, frontend will show success message. If False, frontend will show error message.
        :param on_success_msg: Message if success.
        :param on_error_msg: Message if error.
        :param on_error_msg_simple: Simple message if error.
        :param end_steps: End steps on finalize.
        :return: None
        """

        FinalizeCommand(logger=self, success=success, on_success_msg=on_success_msg, on_error_msg=on_error_msg, on_error_msg_simple=on_error_msg_simple, end_steps=end_steps)

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
    def finalize_msg(self) -> str:
        """
        Get finalize message.

        :return: Finalize message.
        """

        return self._finalize_msg

    @property
    def finalize_msg_simple(self) -> str:
        """
        Get finalize simple message.

        :return: Finalize simple message.
        """

        if self._finalize_msg_simple is None:
            return self._finalize_msg

        return self._finalize_msg_simple

    @property
    def error_occurred(self) -> bool:
        """
        Check if error occurred.

        :return: True if error occurred, otherwise False.
        """

        return self._error_occurred


class ActionSubLoggerContext(LoggingContext):
    def __init__(self,
                 action_logger: "ActionLogger",
                 name: str,
                 title: Optional[str] = None,
                 log_level: Optional[ActionLogAdminSettings.LogLevels] = None,
                 parent: Optional[logging.Logger] = None,
                 formatter: Optional[logging.Formatter] = None,
                 steps: Optional[int] = None,
                 on_success_msg: Optional[str] = None,
                 on_error_msg: Optional[str] = None,
                 end_steps: Optional[bool] = None,
                 show_errors: Optional[bool] = None,
                 halt_on_error: Optional[bool] = None,
                 use_context_logger_level: Optional[bool] = None,
                 use_context_logger_level_on_not_set: Optional[bool] = None,
                 ignore_loggers_equal: Optional[list[str]] = None,
                 ignore_loggers_like: Optional[list[str]] = None,
                 handle_origin_logger: Optional[bool] = None,
                 action_sub_logger_cls: Optional[type[ActionSubLogger]] = None,
                 websocket_handler_cls: Optional[type[WebsocketHandler]] = None):
        """
        Create new action sub logger context manager.

        :param action_logger: Action logger
        :param name: Name of sub logger. Only a-z, A-Z, 0-9, - and _ are allowed.
        :param title: Title of sub logger. Visible in frontend.
        :param log_level: Log level of sub logger. If None, ac
        :param parent: Parent logger. If None, action logger parent will be used.
        :param formatter: Formatter of sub logger. If None, action logger formatter will be used.
        :param steps: Steps of sub logger.
        :param on_success_msg: Message of finalize message if success.
        :param on_error_msg: Message of finalize message if error.
        :param end_steps: End steps on finalize.
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

        # define action logger
        self._action_logger = action_logger

        # set steps
        self._steps = steps

        # set finalize messages
        self.on_success_msg = on_success_msg
        self.on_error_msg = on_error_msg

        # set end steps
        self.end_steps = end_steps

        # set show errors
        if show_errors is None:
            show_errors = action_logger.show_errors
        self.show_errors = show_errors

        # set halt on error
        if halt_on_error is None:
            halt_on_error = action_logger.halt_on_error
        self.halt_on_error = halt_on_error

        # create sub logger
        self.context_logger = self._action_logger.new_sub_logger(name=name,
                                                                 title=title,
                                                                 log_level=log_level,
                                                                 parent=parent,
                                                                 formatter=formatter,
                                                                 action_sub_logger_cls=action_sub_logger_cls,
                                                                 websocket_handler_cls=websocket_handler_cls)

        super().__init__(context_logger=self.context_logger,
                         use_context_logger_level=use_context_logger_level,
                         use_context_logger_level_on_not_set=use_context_logger_level_on_not_set,
                         ignore_loggers_equal=ignore_loggers_equal,
                         ignore_loggers_like=ignore_loggers_like,
                         handle_origin_logger=handle_origin_logger)

    def __enter__(self) -> "ActionSubLogger":
        super().__enter__()
        self.context_logger.start(steps=self._steps)

        return self.context_logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)
        if self.context_logger.exited:
            return False
        else:
            if exc_type is None:
                self.context_logger.finalize(success=True, on_success_msg=self.on_success_msg, on_error_msg=self.on_error_msg, end_steps=self.end_steps)
            else:
                on_error_msg_simple = None
                if exc_type is ActionFailed:
                    on_error_msg = exc_val.args[0]
                else:
                    on_error_msg = None
                    if self.show_errors:
                        # get exception string
                        on_error_msg = traceback.format_exc()
                        on_error_msg_simple = f"{exc_type.__name__}: {exc_val}"
                self.context_logger.finalize(success=False,
                                             on_success_msg=self.on_success_msg,
                                             on_error_msg=on_error_msg,
                                             on_error_msg_simple=on_error_msg_simple,
                                             end_steps=False)
            return exc_type is None or not self.halt_on_error


class ActionLogger:
    _action_loggers: list["ActionLogger"] = []

    def __init__(self,
                 request_or_websocket: Union[Request],
                 log_level: Optional[ActionLogAdminSettings.LogLevels] = None,
                 parent: Optional[logging.Logger] = None,
                 formatter: Union[None, str, logging.Formatter] = None,
                 wait_for_websocket: Optional[bool] = None,
                 wait_for_websocket_timeout: Optional[int] = None,
                 show_errors: Optional[bool] = None,
                 halt_on_error: Optional[bool] = None,
                 use_context_logger_level: Optional[bool] = None,
                 use_context_logger_level_on_not_set: Optional[bool] = None,
                 ignore_loggers_equal: Optional[list[str]] = None,
                 ignore_loggers_like: Optional[list[str]] = None,
                 handle_origin_logger: Optional[bool] = None,
                 action_sub_logger_cls: Optional[type[ActionSubLogger]] = None,
                 websocket_handler_cls: Optional[type[WebsocketHandler]] = None):
        """
        Create new action logger.

        :param request_or_websocket: request or websocket.
        :param log_level: Log level of action logger. If None, parent log level will be used. If parent is None, logging.INFO will be used.
        :param parent: Parent logger. If None, logger will be added to module logger.
        :param formatter: Formatter of action logger. If None, default formatter will be used.
        :param show_errors: Show errors in frontend.
        :param halt_on_error: Halt on error.
        :param wait_for_websocket: Wait for websocket to be connected. For this feature, await must be used.
        :param wait_for_websocket_timeout: Timeout in seconds. For this feature, await must be used.
        """

        # get action log key
        self.action_log_key = self.get_action_key(request_or_websocket=request_or_websocket)

        # get admin
        self.admin = request_or_websocket.app.state.admin

        # get settings
        self.settings: ActionLogAdminSettings = self.admin.settings

        # set log level
        if log_level is None:
            log_level = self.settings.action_log_level
        self.log_level: ActionLogAdminSettings.LogLevels = log_level

        # get parent logger
        if parent is None:
            parent = LOGGER
        self.parent: logging.Logger = parent

        # set formatter
        if formatter is None:
            formatter = self.settings.action_log_formatter
        self.formatter: logging.Formatter = logging.Formatter(formatter)

        # set wait for websocket
        if wait_for_websocket is None:
            wait_for_websocket = self.settings.action_log_wait_for_websocket
        self.wait_for_websocket: bool = wait_for_websocket

        # set wait for websocket timeout
        if wait_for_websocket_timeout is None:
            wait_for_websocket_timeout = self.settings.action_log_wait_for_websocket_timeout
        self.wait_for_websocket_timeout: int = wait_for_websocket_timeout

        # set show errors
        if show_errors is None:
            show_errors = self.settings.action_log_show_errors
        self.show_errors: bool = show_errors

        # set halt on error
        if halt_on_error is None:
            halt_on_error = self.settings.action_log_halt_on_error
        self.halt_on_error: bool = halt_on_error

        # set use context logger level
        if use_context_logger_level is None:
            use_context_logger_level = self.settings.action_log_use_context_logger_level
        self.use_context_logger_level: bool = use_context_logger_level

        # set use context logger level on not set
        if use_context_logger_level_on_not_set is None:
            use_context_logger_level_on_not_set = self.settings.action_log_use_context_logger_level_on_not_set
        self.use_context_logger_level_on_not_set: bool = use_context_logger_level_on_not_set

        # set ignore loggers equal
        if ignore_loggers_equal is None:
            ignore_loggers_equal = self.settings.action_log_ignore_loggers_equal
        self.ignore_loggers_equal: list[str] = ignore_loggers_equal

        # set ignore loggers like
        if ignore_loggers_like is None:
            ignore_loggers_like = self.settings.action_log_ignore_loggers_like
        self.ignore_loggers_like: list[str] = ignore_loggers_like
        if "pymongo" not in self.ignore_loggers_like:
            self.ignore_loggers_like.append("pymongo")  # force ignore loggers like 'pymongo'

        # set handle origin logger
        if handle_origin_logger is None:
            handle_origin_logger = self.settings.action_log_handle_origin_logger
        self.handle_origin_logger: bool = handle_origin_logger

        # set action sub logger class
        self.action_sub_logger_cls = action_sub_logger_cls or ActionSubLogger

        # set websocket handler class
        self.websocket_handler_cls = websocket_handler_cls or WebsocketHandler

        self._sub_logger: list[ActionSubLogger] = []
        self._response_obj: Union[None, bool, ActionLoggerResponse] = None

        # add action logger to action loggers
        self._action_loggers.append(self)

        # get kombu connection
        self._kombu_connection = self.get_kombu_connection(request_or_websocket=request_or_websocket)

        # create exchange and queues from websocket request
        self._exchange, self._start_queue, self._log_queue, self._response_queue, self._download_queue, self._exit_queue = ActionLogger.get_action_log_queues(
            request_or_websocket=request_or_websocket)

        # create producer
        self._producer = self._kombu_connection.Producer(serializer='json')

        # create exit thread
        self._exit_thread_obj = Thread(target=self._exit_thread)

    def __await__(self):
        async def _await() -> "ActionLogger":
            if not self.wait_for_websocket:
                return self

            current_try = 0
            connected = False

            def start_event(body: dict[str, Any], message: Message):
                nonlocal connected
                connected = True

                message.ack()

            with self._kombu_connection.Consumer([self._start_queue], callbacks=[start_event]):
                while len(self._sub_logger) == 0:
                    if connected:
                        break
                    if current_try >= self.wait_for_websocket_timeout:
                        self.exit()
                        raise ValueError("No websocket connected.")

                    current_try += 1
                    LOGGER.debug(f"[{current_try}/{self.wait_for_websocket_timeout}] Waiting for websocket...")
                    await asyncio.sleep(1)

            return self

        return _await().__await__()

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
        finalize_msg = ""
        for sub_logger in self._sub_logger:
            if sub_logger.error_occurred:
                finalize_msg += f"{sub_logger.title}: {sub_logger.finalize_msg_simple}\n"
        if finalize_msg:
            raise ActionFailed(finalize_msg)

    def __del__(self):
        if not self.exited:
            self.exit()

    @classmethod
    def get_action_key(cls, request_or_websocket: Union[Request, WebSocket]) -> str:
        """
        Get action log key from request or websocket.

        :param request_or_websocket: Action log key, request or websocket.
        :return: Action log key.
        """

        if isinstance(request_or_websocket, Request):
            action_log_key = request_or_websocket.query_params.get("action_log_key", None)
            if action_log_key is None:
                action_log_key = request_or_websocket.path_params.get("action_log_key", None)
            if action_log_key is None:
                raise ValueError("No action log key provided.")
        elif isinstance(request_or_websocket, WebSocket):
            action_log_key = request_or_websocket.path_params.get("action_log_key", None)
            if action_log_key is None:
                raise ValueError("No action log key provided.")
        else:
            raise ValueError("Invalid action log key or request.")
        return action_log_key

    @classmethod
    def get_kombu_connection(cls, request_or_websocket: Union[Request, WebSocket]) -> Connection:
        return request_or_websocket.app.state.admin.kombu_connection

    @classmethod
    def get_action_log_exchange(cls, request_or_websocket: Union[Request, WebSocket]) -> Exchange:
        exchange = Exchange(KOMBU_EXCHANGE_NAME, "direct", durable=True)
        exchange = exchange.bind(cls.get_kombu_connection(request_or_websocket))
        exchange.declare()
        return exchange

    @classmethod
    def get_action_log_queues(cls, request_or_websocket: Union[Request, WebSocket]) -> tuple[Exchange, Queue, Queue, Queue, Queue, Queue]:
        # get kombu connection
        connection = cls.get_kombu_connection(request_or_websocket=request_or_websocket)

        # get action log exchange
        exchange = cls.get_action_log_exchange(request_or_websocket=request_or_websocket)

        # get action log key
        action_log_key = cls.get_action_key(request_or_websocket)

        # create exit queue
        start_queue_name = f"{action_log_key}_start"
        start_queue = Queue(start_queue_name, exchange=exchange, routing_key=start_queue_name)
        start_queue = start_queue.bind(connection)
        start_queue.declare()

        # create log queue
        log_queue_name = f"{action_log_key}_log"
        log_queue = Queue(log_queue_name, exchange=exchange, routing_key=log_queue_name)
        log_queue = log_queue.bind(connection)
        log_queue.declare()

        # create response queue
        response_queue_name = f"{action_log_key}_response"
        response_queue = Queue(response_queue_name, exchange=exchange, routing_key=response_queue_name)
        response_queue = response_queue.bind(connection)
        response_queue.declare()

        # create download queue
        download_queue_name = f"{action_log_key}_download"
        download_queue = Queue(download_queue_name, exchange=exchange, routing_key=download_queue_name)
        download_queue = download_queue.bind(connection)
        download_queue.declare()

        # create exit queue
        exit_queue_name = f"{action_log_key}_exit"
        exit_queue = Queue(exit_queue_name, exchange=exchange, routing_key=exit_queue_name)
        exit_queue = exit_queue.bind(connection)
        exit_queue.declare()

        return exchange, start_queue, log_queue, response_queue, download_queue, exit_queue

    @classmethod
    def parse_response_obj(cls, data: Union[str, dict[str, Any]]) -> Union[None, ActionLoggerResponse]:
        """
        Parse response object.

        :param data: Data
        :return: Response object
        """

        # parse to dict
        if type(data) is str:
            try:
                data = json.loads(data)
            except json.JSONDecodeError as e:
                LOGGER.error(f"JSONDecodeError while parsing response object: {e}")
                return None

        # create response object
        try:
            response_obj = ActionLoggerResponse(**data)
        except ValidationError as e:
            LOGGER.error(f"ValidationError while parsing response object: {e}")
            return None

        return response_obj

    def new_sub_logger(self,
                       name: str,
                       title: Optional[str] = None,
                       log_level: Optional[ActionLogAdminSettings.LogLevels] = None,
                       parent: Optional[logging.Logger] = None,
                       formatter: Optional[logging.Formatter] = None,
                       action_sub_logger_cls: Optional[type[ActionSubLogger]] = None,
                       websocket_handler_cls: Optional[type[WebsocketHandler]] = None) -> ActionSubLogger:
        """
        Create new sub logger.

        :param name: Name of sub logger. Only a-z, A-Z, 0-9, - and _ are allowed.
        :param title: Title of sub logger. Visible in frontend.
        :param log_level: Log level of sub logger. If None, action logger log level will be used.
        :param parent: Parent logger. If None, action logger parent will be used.
        :param formatter: Formatter of sub logger. If None, action logger formatter will be used.
        :param action_sub_logger_cls: Action sub logger class.
        :param websocket_handler_cls: Websocket handler class.
        :return: Sub logger.
        """

        try:
            self.get_sub_logger(sub_logger_name=name)
        except ValueError:
            pass

        # create sub logger
        action_sub_logger_cls = action_sub_logger_cls or self.action_sub_logger_cls
        sub_logger = action_sub_logger_cls(action_logger=self,
                                           name=name,
                                           title=title,
                                           parent=parent,
                                           log_level=log_level,
                                           formatter=formatter,
                                           websocket_handler_cls=websocket_handler_cls)

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
                   log_level: Optional[ActionLogAdminSettings.LogLevels] = None,
                   parent: Optional[logging.Logger] = None,
                   formatter: Optional[logging.Formatter] = None,
                   steps: Optional[int] = None,
                   on_success_msg: Optional[str] = None,
                   on_error_msg: Optional[str] = None,
                   end_steps: Optional[bool] = None,
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
        :param end_steps: End steps on finalize.
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
                                      end_steps=end_steps,
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

    def confirm(self, text: str, submit_btn_text: Optional[str] = None, form: Optional[str] = None) -> ConfirmCommand:
        """
        Send confirm form to frontend.

        :param text: Text of confirm form.
        :param submit_btn_text: Text of submit button.
        :param form: Form HTML.
        :return: Form data.
        """

        return ConfirmCommand(logger=self, text=text, submit_btn_text=submit_btn_text, form=form)

    def download(self, file_path: Union[str, Path], text: str, icon: Optional[str] = None, submit_btn_text: Optional[str] = None,
                 form: Optional[str] = None) -> DownloadCommand:
        """
        Send download form to frontend.

        :param file_path: File path
        :param text: Text of download form.
        :param icon: Icon of download form.
        :param submit_btn_text: Text of submit button.
        :param form: Form HTML.
        :return: Form data.
        """

        return DownloadCommand(logger=self, file_path=file_path, text=text, icon=icon, submit_btn_text=submit_btn_text, form=form)

    def yes_no(self, text: str, submit_btn_text: Optional[str] = None, abort_btn_text: Optional[str] = None, form: Optional[str] = None) -> YesNoCommand:
        """
        Send yes/no form to frontend.

        :param text: Text of yes/no form.
        :param submit_btn_text: Text of submit button.
        :param abort_btn_text: Text of cancel button.
        :param form: Form HTML.
        :return: Form data.
        """

        return YesNoCommand(logger=self, text=text, submit_btn_text=submit_btn_text, abort_btn_text=abort_btn_text, form=form)

    @classmethod
    async def _form_data(cls, logger: Union["ActionLogger", ActionSubLogger], timeout: Optional[float] = None) -> Union[bool, dict[str, Any]]:
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

    async def form_data(self, timeout: Optional[float] = None) -> Union[bool, dict[str, Any]]:
        """
        Fetch form data from frontend.

        :param timeout: Timeout in seconds.
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

        # exit sub loggers
        for sub_logger in self._sub_logger:
            if not sub_logger.exited:
                sub_logger.exit()

        # remove action logger from action loggers
        self._action_loggers.remove(self)

        # exit thread
        self._exit_thread_obj.start()

    def _exit_thread(self):
        """
        Exit thread.

        :return: None
        """

        exited = False

        def exit_event(body: dict[str, Any], message: Message):
            nonlocal exited

            exited = True
            message.ack()

        with self._kombu_connection.Consumer([self._exit_queue], callbacks=[exit_event]):
            while not exited:
                try:
                    self._kombu_connection.drain_events(timeout=5)
                except socket_timeout:
                    if not exited:
                        warn(f"Exiting action logger {self.action_log_key} timed out.", UserWarning)
                        exited = True
                if exited:
                    break

        # delete queues
        self._start_queue.delete()
        self._log_queue.delete()
        self._response_queue.delete()
        self._download_queue.delete()
        self._exit_queue.delete()

    @property
    def exited(self) -> bool:
        """
        Check if action logger is exited.

        :return: True if exited, otherwise False.
        """

        return self not in self._action_loggers

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

        # convert command to dict
        command_dict = command.model_dump()

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
            ...

        self._producer.publish(command_dict, exchange=self._exchange, routing_key=self._log_queue.name)

    @classmethod
    async def _await_response(cls, logger: Union["ActionLogger", ActionSubLogger], timeout: Optional[float] = None) -> Union[bool, ActionLoggerResponse]:
        if not isinstance(logger, ActionLogger) and not isinstance(logger, ActionSubLogger):
            raise ValueError("Invalid logger.")

        if not logger.awaiting_response:
            raise ValueError("Logger is not awaiting form data.")

        action_logger = logger if isinstance(logger, ActionLogger) else logger.action_logger

        # wait for response
        start_wait = time.perf_counter()
        with action_logger._kombu_connection.Consumer([action_logger._response_queue], callbacks=[action_logger.send_response_to_logger]):
            while logger.awaiting_response:
                try:
                    action_logger._kombu_connection.drain_events(timeout=0.001)
                except socket_timeout:
                    ...
                await asyncio.sleep(0.001)
                if timeout is None:
                    continue
                if time.perf_counter() - start_wait >= timeout:
                    return False

        # get response object
        response_obj = getattr(logger, "_response_obj")
        setattr(logger, "_response_obj", None)
        logger_name = getattr(logger, "sub_logger_name", "")

        # check is response object is for this logger
        if not response_obj.sub_logger == logger_name:
            raise ValueError("The response object is not for this logger.")

        return response_obj

    async def await_response(self, timeout: Optional[float] = None) -> Union[bool, ActionLoggerResponse]:
        """
        Fetch response from frontend.

        :param timeout: Timeout in seconds.
        :return: Form data.
        """

        return await self._await_response(logger=self, timeout=timeout)

    def send_response_to_logger(self, body: dict[str, Any], message: Message) -> None:
        """
        Send response object to logger or sub logger.

        :param body: Body
        :param message: Message
        :return: None
        """

        message.ack()

        response_obj = self.parse_response_obj(body)

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
