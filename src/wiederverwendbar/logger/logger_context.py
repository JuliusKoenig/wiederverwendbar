import inspect
import logging
from typing import Union

from wiederverwendbar.logger.logger_singleton import SubLogger


class LoggingContext:
    class WrappedHandle:
        def __init__(self, saved_handle_method: callable):
            self.saved_handle_method = saved_handle_method
            self.contexts = []

        def __call__(self, logger, *args, **kwargs) -> None:
            # get stack
            stack = inspect.stack()[3:]

            # get all LoggingContexts in stack
            logging_contexts = []
            for frame_info in stack:
                frame = frame_info.frame
                for var in frame.f_locals.values():
                    if isinstance(var, LoggingContext):
                        if var.exited:
                            continue
                        logging_contexts.append(var)

            # filter out LoggingContexts that are not in self.contexts
            logging_contexts = [logging_context for logging_context in logging_contexts if logging_context in self.contexts]

            # raise error if logging_contexts is empty <- this should never happen
            if len(logging_contexts) == 0:
                raise RuntimeError("logging_contexts is empty")

            # check if some LoggingContexts need update
            for logging_context in logging_contexts:
                if logging_context.need_update:
                    logging_context.update()

            # get all loggers from logging_contexts
            context_loggers = [logging_context.context_logger for logging_context in logging_contexts]

            # handle to all logging_contexts
            for context_logger in context_loggers:
                # get context_logger class
                context_logger_type = type(context_logger)

                # get handle method of context_logger_type
                handle_method = getattr(context_logger_type, "handle")

                self.handle(handle_method, context_logger, *args, **kwargs)

            # handle with self.logger
            if logging_contexts[-1].handle_origin_logger:
                self.handle(self.saved_handle_method, *args, **kwargs)

        @classmethod
        def handle(cls, handle_method: callable, *args, **kwargs) -> None:
            # get signature of logger.handle
            signature = inspect.signature(handle_method)

            # bind signature to logger.handle
            bound_signature = signature.bind(*args, **kwargs)

            # handle with bound signature
            handle_method(**bound_signature.arguments)

    class ContextLogger(logging.Logger):
        def __new__(cls, *args, **kwargs):
            # get logging_contexts
            # get stack
            stack = inspect.stack()

            # get all LoggingContexts in stack
            logging_contexts = []
            for frame_info in stack:
                frame = frame_info.frame
                for var in frame.f_locals.values():
                    if isinstance(var, LoggingContext):
                        if var.exited:
                            continue
                        logging_contexts.append(var)

            # get logger class before context
            logger_class_before_context = None
            for logging_context in logging_contexts:
                _logger_class_before_context = logging_context._logger_class_before_context
                if _logger_class_before_context != cls:
                    if logger_class_before_context is not None and logger_class_before_context != _logger_class_before_context:
                        raise RuntimeError("logger_class_before_context is not None")
                    logger_class_before_context = _logger_class_before_context
            if logger_class_before_context is None:
                raise RuntimeError("logger_class_before_context is None")

            # use logger_class_before_context to build logger type
            logger = super().__new__(logger_class_before_context)

            # call __init__ of logger
            logger.__init__(*args, **kwargs)

            # update all logging contexts with logger
            for logging_context in logging_contexts:
                logging_context.update_one(logger)

            # set context_logger marker
            if isinstance(logger, SubLogger):
                with logger.reconfigure():
                    setattr(logger, "created_context_logger", True)
            else:
                setattr(logger, "created_context_logger", True)

            return logger

    def __init__(self, context_logger: logging.Logger, handle_origin_logger: bool = True):
        self.context_logger = context_logger

        # set context_logger marker
        if isinstance(self.context_logger, SubLogger):
            with self.context_logger.reconfigure():
                setattr(self.context_logger, "context_logger", True)
        else:
            setattr(self.context_logger, "context_logger", True)

        self.handle_origin_logger = handle_origin_logger
        self._exited = False
        self._wrapped_loggers: Union[tuple, tuple[logging.Logger]] = ()

        # get all loggers except context logger to prevent that existing loggers are ContextLogger
        self._get_all_loggers()

        # get current logger class
        self._logger_class_before_context = logging.getLoggerClass()
        if self._logger_class_before_context != LoggingContext.ContextLogger:
            logging.setLoggerClass(LoggingContext.ContextLogger)

    def __enter__(self) -> "LoggingContext":
        self.update()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        # reset _log method for all loggers
        for logger in self.wrapped_loggers:
            # get logger's handle method
            wrapped_handle: LoggingContext.WrappedHandle = getattr(logger, "handle")

            # skip if not wrapped
            if not hasattr(wrapped_handle, "saved_handle_method"):
                continue

            # raise error if context not in contexts
            if self not in wrapped_handle.contexts:
                raise RuntimeError(f"{self} is not in contexts")

            # remove context from wrapped_handle
            wrapped_handle.contexts.remove(self)

            # restore logger's handle method
            if len(wrapped_handle.contexts) == 0:
                if isinstance(logger, SubLogger):
                    with logger.reconfigure():
                        setattr(logger, "handle", wrapped_handle.saved_handle_method)
                else:
                    setattr(logger, "handle", wrapped_handle.saved_handle_method)

            # delete created_context_logger
            if getattr(logger, "created_context_logger", False):
                if logger.name in logging.root.manager.loggerDict:
                    logging.root.manager.loggerDict.pop(logger.name)

        # restore logger class
        if self._logger_class_before_context != LoggingContext.ContextLogger:
            logging.setLoggerClass(self._logger_class_before_context)

        # reset attributes
        self._wrapped_loggers = ()
        self._exited = True

    def _get_all_loggers(self) -> list[logging.Logger]:
        all_loggers = []
        for name in logging.root.manager.loggerDict:
            logger = logging.getLogger(name)
            # skip if self
            if logger == self.context_logger:
                continue
            # skip if logger is a context logger
            if getattr(logger, "context_logger", False):
                continue
            all_loggers.append(logger)
        return all_loggers

    @property
    def exited(self) -> bool:
        return self._exited

    @property
    def wrapped_loggers(self) -> Union[tuple, tuple[logging.Logger]]:
        return self._wrapped_loggers

    @property
    def need_update(self) -> bool:
        return not self._exited and len(self._wrapped_loggers) != len(self._get_all_loggers())

    def update(self) -> None:
        if self._exited:
            raise RuntimeError(f"{self} is already exited")

        # get all loggers except context logger
        all_loggers = self._get_all_loggers()

        # set _log method for all loggers
        for logger in all_loggers:
            self.update_one(logger)

    def update_one(self, logger: logging.Logger):
        wrapped_loggers = list(self._wrapped_loggers)

        # get logger's handle method
        logger_handle = getattr(logger, "handle")

        # check if already wrapped
        if hasattr(logger_handle, "saved_handle_method"):
            wrapped_handle: LoggingContext.WrappedHandle = logger_handle
            logger_handle = None
        else:
            wrapped_handle: LoggingContext.WrappedHandle = LoggingContext.WrappedHandle(logger_handle)

        # append context to wrapped_handle
        if self in wrapped_handle.contexts:
            return

        wrapped_handle.contexts.append(self)
        wrapped_loggers.append(logger)

        # overwrite logger's handle method
        if logger_handle is not None:
            if isinstance(logger, SubLogger):
                with logger.reconfigure():
                    setattr(logger, "handle", type(logger_handle)(wrapped_handle, logger))
            else:
                setattr(logger, "handle", type(logger_handle)(wrapped_handle, logger))

        self._wrapped_loggers = tuple(wrapped_loggers)
