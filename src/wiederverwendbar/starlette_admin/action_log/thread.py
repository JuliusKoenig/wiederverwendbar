import asyncio
import logging
import threading
import time
from typing import Optional

from wiederverwendbar.starlette_admin.action_log.logger import ActionLogger


class ActionThread(threading.Thread):
    def __init__(self,
                 action_logger: ActionLogger,
                 name: str,
                 payload: Optional[callable] = None,
                 payload_args: Optional[list] = None,
                 payload_kwargs: Optional[dict] = None,
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
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)

        self._payload = payload
        self._payload_args = payload_args if payload_args is not None else []
        self._payload_kwargs = payload_kwargs if payload_kwargs is not None else {}

        self._action_logger = action_logger
        self._sub_logger = None

        self._name = name
        self._title = title
        self._log_level = log_level
        self._parent = parent
        self._formatter = formatter
        self._steps = steps
        self._on_success_msg = on_success_msg
        self._on_error_msg = on_error_msg
        self._show_errors = show_errors
        self._halt_on_error = halt_on_error
        self._use_context_logger_level = use_context_logger_level
        self._use_context_logger_level_on_not_set = use_context_logger_level_on_not_set
        self._ignore_loggers_equal = ignore_loggers_equal
        self._ignore_loggers_like = ignore_loggers_like
        self._handle_origin_logger = handle_origin_logger

    def run(self):
        with self._action_logger.sub_logger(name=self._name,
                                            title=self._title,
                                            log_level=self._log_level,
                                            parent=self._parent,
                                            formatter=self._formatter,
                                            steps=self._steps,
                                            on_success_msg=self._on_success_msg,
                                            on_error_msg=self._on_error_msg,
                                            show_errors=self._show_errors,
                                            halt_on_error=self._halt_on_error,
                                            use_context_logger_level=self._use_context_logger_level,
                                            use_context_logger_level_on_not_set=self._use_context_logger_level_on_not_set,
                                            ignore_loggers_equal=self._ignore_loggers_equal,
                                            ignore_loggers_like=self._ignore_loggers_like,
                                            handle_origin_logger=self._handle_origin_logger) as sub_logger:
            self._sub_logger = sub_logger
            result = self.payload()
            self._sub_logger.finalize(success=result)

    async def wait(self, timeout: int = -1):
        start_wait = time.perf_counter()
        while self.is_alive():
            if timeout != -1:
                if time.perf_counter() - start_wait > timeout:
                    self._sub_logger.finalize(success=False, on_error_msg="Thread timed out.")
            await asyncio.sleep(0.1)

    def payload(self) -> bool:
        if self._payload is None:
            raise NotImplementedError("Payload not implemented.")
        return self._payload(*self._payload_args, **self._payload_kwargs)
