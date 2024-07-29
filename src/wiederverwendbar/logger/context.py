import inspect
import logging
from typing import Union, Optional

from wiederverwendbar.logger.singleton import SubLogger

# get module lock
_acquireLock = getattr(logging, "_acquireLock")
_releaseLock = getattr(logging, "_releaseLock")


class LoggingContext:
    class WrappedHandle:
        def __init__(self, saved_handle_method: callable, saved_level):
            self.saved_level = saved_level
            self.saved_handle_method = saved_handle_method
            self.contexts = []

        def __call__(self, logger, *args, **kwargs) -> None:
            # get all LoggingContexts in stack
            logging_contexts = LoggingContext.get_from_stack(inspect.stack()[3:])

            # filter out LoggingContexts that are not in self.contexts
            logging_contexts = [logging_context for logging_context in logging_contexts if logging_context in self.contexts]

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

            # get handle_origin_logger from last LoggingContext
            handle_origin_logger = True
            if len(logging_contexts) > 0:
                handle_origin_logger = logging_contexts[-1].handle_origin_logger

            # handle to origin logger
            if handle_origin_logger:
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
            logging_contexts = LoggingContext.get_from_stack(inspect.stack())

            # get logger class before context
            logger_class_before_context = None
            for logging_context in logging_contexts:
                _logger_class_before_context = logging_context._logger_class_before_context
                if _logger_class_before_context != cls:
                    if logger_class_before_context is not None and logger_class_before_context != _logger_class_before_context:
                        raise RuntimeError("logger_class_before_context is not None")
                    logger_class_before_context = _logger_class_before_context
            if logger_class_before_context is None:
                # context logger is initialized without LoggingContext
                logger = super().__new__(cls)
            else:
                # use logger_class_before_context to build logger type
                logger = super().__new__(logger_class_before_context)

            # call __init__ of logger
            logger.__init__(*args, **kwargs)

            # update all logging contexts with logger
            for logging_context in logging_contexts:
                # check if logger is in ignore_loggers_equal
                if logger.name in logging_context.ignore_loggers_equal:
                    continue
                # check if logger is in ignore_loggers_like
                if any([ignore_logger in logger.name for ignore_logger in logging_context.ignore_loggers_like]):
                    continue
                logging_context.update_one(logger)

            # set context_logger marker
            if isinstance(logger, SubLogger):
                with logger.reconfigure():
                    setattr(logger, "created_context_logger", True)
            else:
                setattr(logger, "created_context_logger", True)

            return logger

    def __init__(self,
                 context_logger: logging.Logger,
                 use_context_logger_level: bool = True,
                 use_context_logger_level_on_not_set: Optional[bool] = None,
                 ignore_loggers_equal: Optional[list[str]] = None,
                 ignore_loggers_like: Optional[list[str]] = None,
                 handle_origin_logger: bool = True):
        self.context_logger = context_logger

        # set context_logger marker
        if isinstance(self.context_logger, SubLogger):
            with self.context_logger.reconfigure():
                setattr(self.context_logger, "context_logger", True)
        else:
            setattr(self.context_logger, "context_logger", True)

        self.handle_origin_logger = handle_origin_logger
        self._use_context_logger_level = use_context_logger_level
        if use_context_logger_level_on_not_set is None:
            use_context_logger_level_on_not_set = use_context_logger_level
        self._use_context_logger_level_on_not_set = use_context_logger_level_on_not_set
        if ignore_loggers_equal is None:
            ignore_loggers_equal = []
        self.ignore_loggers_equal = ignore_loggers_equal
        if ignore_loggers_like is None:
            ignore_loggers_like = []
        self.ignore_loggers_like = ignore_loggers_like
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

        # find the frame where the context manager is used
        context_frame_index = None
        stack = inspect.stack()
        for i, frame_info in enumerate(stack):
            if "with" in frame_info.code_context[0] and frame_info.function != "__enter__":
                context_frame_index = i
                break
        if context_frame_index is None:
            raise RuntimeError("context_frame_index is None")

        # check if the context manager var is defined in the context frame
        no_context_var = False
        if self.__class__ != LoggingContext:
            no_context_var = True
        else:
            if "as" not in stack[context_frame_index].code_context[0]:
                no_context_var = True

        # get random variable name not used in the context frame
        if no_context_var:
            while True:
                var_name = f"logging_context_{id(self)}"
                if var_name not in stack[context_frame_index].frame.f_locals:
                    break

            stack[context_frame_index].frame.f_locals[var_name] = self

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.restore()

        # restore logger class
        if self._logger_class_before_context != LoggingContext.ContextLogger:
            logging.setLoggerClass(self._logger_class_before_context)

        # reset attributes
        self._exited = True

    def _get_all_loggers(self) -> list[logging.Logger]:
        all_loggers = []
        for name in list(logging.root.manager.loggerDict):
            logger = logging.getLogger(name)
            # skip if self
            if logger == self.context_logger:
                continue
            # skip if logger is a context logger
            if getattr(logger, "context_logger", False):
                continue
            # skip if logger is in ignore_loggers_equal
            if logger.name in self.ignore_loggers_equal:
                continue
            # skip if logger is in ignore_loggers_like
            if any([ignore_logger in logger.name for ignore_logger in self.ignore_loggers_like]):
                continue
            all_loggers.append(logger)
        return all_loggers

    @classmethod
    def get_from_stack(cls, stack: list[inspect.FrameInfo]) -> list["LoggingContext"]:
        logging_contexts = []
        for frame_info in stack:
            frame = frame_info.frame
            for var in list(frame.f_locals.values()):
                if isinstance(var, LoggingContext):
                    if var.exited:
                        continue
                    logging_contexts.append(var)
        return logging_contexts

    @property
    def exited(self) -> bool:
        return self._exited

    @property
    def wrapped_loggers(self) -> Union[tuple, tuple[logging.Logger]]:
        return self._wrapped_loggers

    @property
    def need_update(self) -> bool:
        if self._exited:
            return False
        # check if all loggers are wrapped
        for logger in self._get_all_loggers():
            if logger not in self._wrapped_loggers:
                return True

        # check if some loggers have different level
        if self._use_context_logger_level or self._use_context_logger_level_on_not_set:
            for logger in self._wrapped_loggers:
                if self._use_context_logger_level and logger.level != self.context_logger.level:
                    return True
                if self._use_context_logger_level_on_not_set and logger.level == logging.NOTSET:
                    return True

        return False

    def update(self) -> None:
        if self._exited:
            raise RuntimeError(f"{self} is already exited")

        # get all loggers except context logger
        all_loggers = self._get_all_loggers()

        # set _log method for all loggers
        for logger in all_loggers:
            self.update_one(logger)

    def update_one(self, logger: logging.Logger):
        try:
            # get module lock
            _acquireLock()

            wrapped_loggers = list(self._wrapped_loggers)

            # use logger's level
            saved_level = logger.level
            if self._use_context_logger_level or (self._use_context_logger_level_on_not_set and logger.level == logging.NOTSET):
                logger.setLevel(self.context_logger.level)

            # get logger's handle method
            logger_handle = getattr(logger, "handle")

            # check if already wrapped
            if hasattr(logger_handle, "saved_handle_method"):
                wrapped_handle: LoggingContext.WrappedHandle = logger_handle
                logger_handle = None
            else:
                wrapped_handle: LoggingContext.WrappedHandle = LoggingContext.WrappedHandle(logger_handle, saved_level)

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
        finally:
            # release module lock
            _releaseLock()

    def restore(self) -> None:
        """
        Restore all wrapped loggers

        :return: None
        """

        while len(self._wrapped_loggers) > 0:
            logger = self._wrapped_loggers[0]
            self.restore_one(logger)
            self._wrapped_loggers = self._wrapped_loggers[1:]

    def restore_one(self, logger: logging.Logger) -> None:
        try:
            # get module lock
            _acquireLock()

            # get logger's handle method
            wrapped_handle: LoggingContext.WrappedHandle = getattr(logger, "handle")

            # raise error if not wrapped
            if not hasattr(wrapped_handle, "saved_handle_method"):
                raise RuntimeError(f"{logger} is not wrapped")

            # raise error if context not in contexts
            if self not in wrapped_handle.contexts:
                raise RuntimeError(f"{self} is not in contexts")

            # remove context from wrapped_handle
            wrapped_handle.contexts.remove(self)

            if len(wrapped_handle.contexts) == 0:
                # restore logger's level
                if self._use_context_logger_level or self._use_context_logger_level_on_not_set:
                    logger.setLevel(wrapped_handle.saved_level)

                # restore logger's handle method
                if isinstance(logger, SubLogger):
                    with logger.reconfigure():
                        setattr(logger, "handle", wrapped_handle.saved_handle_method)
                else:
                    setattr(logger, "handle", wrapped_handle.saved_handle_method)

            # delete created_context_logger
            if getattr(logger, "created_context_logger", False):
                if logger.name in logging.root.manager.loggerDict:
                    logging.root.manager.loggerDict.pop(logger.name)
        finally:
            # release module lock
            _releaseLock()
