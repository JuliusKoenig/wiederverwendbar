import ctypes as _ctypes
import logging as _logging
import sys as _sys
import threading as _threading
import time as _time
import traceback as _traceback
from collections.abc import Callable as _Callable
from contextlib import contextmanager as _contextmanager
from datetime import datetime as _datetime
from typing import Optional as _Optional, Any as _Any, Union as _Union

from wiederverwendbar.functions.datetime import local_now as _local_now


class ThreadInterrupt(_threading.ThreadError):
    """
    Exception to interrupt a thread.
    """

    ...


class ThreadLoopContinue(_threading.ThreadError):
    """
    Exception to continue a loop in a thread.
    """

    ...


class ThreadStop(_threading.ThreadError):
    """
    Exception to stop a thread.
    """

    ...


class ThreadKill(_threading.ThreadError):
    """
    Exception to kill a thread.
    """

    ...


class ThreadWatchdogError(_threading.ThreadError):
    """
    Exception to indicate an error in the watchdog of a thread.
    """

    ...


class ExtendedThread(_threading.Thread):
    """
    Extended thread class with additional features.

    Features:
    - Logging
    - Interrupt handling
    - Loop handling
    - Stop handling
    - Kill handling
    - Watchdog
    - Auto start
    - Context manager for ignore
    - Context manager for loop wait
    - Thread safe properties
    """

    def __init__(self,
                 group=None,
                 target: _Optional[_Callable[..., _Any]] = None,
                 name: _Optional[str] = None,
                 args: tuple[_Any, ...] = (),
                 kwargs: dict[str, _Any] = None,
                 *,
                 daemon: _Optional[bool] = None,
                 cls_name: _Optional[str] = None,
                 logger: _Optional[_logging.Logger] = None,
                 ignore_stop: _Optional[bool] = None,
                 loop_disabled: _Optional[bool] = None,
                 loop_sleep_time: _Optional[float] = None,
                 loop_stop_on_other_exception: _Optional[bool] = None,
                 continue_exceptions: _Optional[list[type[BaseException]]] = None,
                 stop_exceptions: _Optional[list[type[BaseException]]] = None,
                 kill_exceptions: _Optional[list[type[BaseException]]] = None,
                 watchdog_target: _Optional[_Callable[["ExtendedThread"], bool]] = None,
                 auto_start: _Optional[bool] = None):
        """
        Initialize the extended thread.

        :param group: Thread group.
        :param target: Thread target.
        :param name: Thread name.
        :param args: Thread arguments.
        :param kwargs: Thread keyword arguments.
        :param daemon: Thread daemon.
        :param cls_name: Class name used in the logger.
        :param logger: The logger of the thread.
        :param ignore_stop: If the stop should be ignored.
        :param loop_disabled: If the loop is disabled.
        :param loop_sleep_time: Loop sleep time.
        :param loop_stop_on_other_exception: If the loop should stop on other exceptions.
        :param continue_exceptions: Exceptions to continue the loop.
        :param stop_exceptions: Exceptions to stop the thread.
        :param kill_exceptions: Exceptions to kill the thread.
        :param watchdog_target: Watchdog target.
        :param auto_start: If the thread should start automatically.
        """

        super().__init__(
            group=group,
            target=target,
            name=name,
            args=args,
            kwargs=kwargs,
            daemon=daemon
        )
        self.lock = _threading.Lock()

        # set class name
        if cls_name is None:
            cls_name = self.__class__.__name__
        self._cls_name: str = cls_name

        # set logger
        if logger is None:
            # create a logger if none is provided
            logger = _logging.getLogger(self.name)
        self._logger: _logging.Logger = logger

        # set ignore stop
        if ignore_stop is None:
            ignore_stop = False
        self._ignore_stop: bool = ignore_stop

        # set loop disabled
        if loop_disabled is None:
            loop_disabled = False
        self._loop_disabled: bool = loop_disabled

        # set loop delay
        self._loop_sleep_time: _Optional[float] = loop_sleep_time

        # set loop stop on other exception
        if loop_stop_on_other_exception is None:
            loop_stop_on_other_exception = False
        self._loop_stop_on_other_exception: bool = loop_stop_on_other_exception

        # set continue exceptions
        if continue_exceptions is None:
            continue_exceptions = []
        if ThreadLoopContinue not in continue_exceptions:
            continue_exceptions.append(ThreadLoopContinue)
        self._continue_exceptions: tuple[type[BaseException]] = tuple(continue_exceptions)

        # set stop exceptions
        if stop_exceptions is None:
            stop_exceptions = []
        if ThreadStop not in stop_exceptions:
            stop_exceptions.append(ThreadStop)
        self._stop_exceptions: tuple[type[BaseException]] = tuple(stop_exceptions)

        # set kill exceptions
        if kill_exceptions is None:
            kill_exceptions = []
        if ThreadKill not in kill_exceptions:
            kill_exceptions.append(ThreadKill)
        self._kill_exceptions: tuple[type[BaseException]] = tuple(kill_exceptions)

        # set watchdog target
        self._watchdog_target: _Optional[_Callable[["ExtendedThread"], bool]] = watchdog_target

        # set auto start
        if auto_start is None:
            auto_start = True
        self._auto_start: bool = auto_start

        # set internal variables
        self._started_at: _Optional[_datetime] = None
        self._ended_at: _Optional[_datetime] = None
        self._loop_started_at: _Optional[_datetime] = None
        self._loop_ended_at: _Optional[_datetime] = None
        self._loop_delay: float = 0.0
        self._wait: bool = False
        self._interrupt_exception: _Optional[BaseException] = None
        self._watchdog_thread: _Optional[_threading.Thread] = None

        if self._auto_start:
            self.start()

    def __del__(self):
        if self.is_alive():
            self.stop()

    @property
    def logger(self) -> _logging.Logger:
        """
        Get the logger of the thread.

        :rtype: logging.Logger
        :return: The logger of the thread.
        """

        with self.lock:
            return self._logger

    @logger.setter
    def logger(self, value: _logging.Logger):
        """
        Set the logger of the thread.

        :param value: The new logger.
        :rtype: None
        """

        with self.lock:
            self._logger = value

    @property
    def started_at(self) -> _Optional[_datetime]:
        """
        Get the time when the thread was started.

        :rtype: datetime.datetime
        :return: The time when the thread was started.
        """

        with self.lock:
            return self._started_at

    @property
    def loop_started_at(self) -> _Optional[_datetime]:
        """
        Get the time when the loop was started.

        :rtype: datetime.datetime
        :return: The time when the loop was started.
        """

        with self.lock:
            return self._loop_started_at

    @property
    def loop_ended_at(self) -> _Optional[_datetime]:
        """
        Get the time when the loop was ended.

        :rtype: datetime.datetime
        :return: The time when the loop was ended.
        """

        with self.lock:
            return self._loop_ended_at

    @property
    def ended_at(self) -> _Optional[_datetime]:
        """
        Get the time when the thread was ended.

        :rtype: datetime.datetime
        :return: The time when the thread was ended.
        """

        with self.lock:
            return self._ended_at

    @property
    def ignore_stop(self) -> bool:
        """
        If the stop should be ignored.

        :rtype: bool
        :return: True if the stop should be ignored.
        """

        with self.lock:
            return self._ignore_stop

    @ignore_stop.setter
    def ignore_stop(self, value: bool):
        """
        Set if the stop should be ignored.

        :param value: If the stop should be ignored.
        :rtype: None
        """

        with self.lock:
            self._ignore_stop = value

    @property
    def loop_disabled(self) -> bool:
        """
        If the loop is disabled.

        :rtype: bool
        :return: True if the loop is disabled.
        """

        with self.lock:
            return self._loop_disabled

    @property
    def loop_sleep_time(self) -> _Optional[float]:
        """
        Get the loop sleep time.

        :rtype: float
        :return: The loop sleep time.
        """

        with self.lock:
            return self._loop_sleep_time

    @loop_sleep_time.setter
    def loop_sleep_time(self, value: _Optional[float]):
        """
        Set the loop sleep time.

        :param value: The loop sleep time.
        :rtype: None
        """

        with self.lock:
            self._loop_sleep_time = value

    @property
    def loop_delay(self) -> float:
        """
        Get the loop delay.

        :rtype: float
        :return: The loop delay.
        """

        with self.lock:
            return self._loop_delay

    @property
    def loop_stop_on_other_exception(self) -> bool:
        """
        If the loop should stop on other exceptions.

        :rtype: bool
        :return: True if the loop should stop on other exceptions.
        """

        with self.lock:
            return self._loop_stop_on_other_exception

    @loop_stop_on_other_exception.setter
    def loop_stop_on_other_exception(self, value: bool):
        """
        Set if the loop should stop on other exceptions.

        :param value: If the loop should stop on other exceptions.
        :rtype: None
        """

        with self.lock:
            self._loop_stop_on_other_exception = value

    @property
    def wait(self) -> bool:
        """
        If the thread should wait.

        :rtype: bool
        :return: True if the thread should wait.
        """

        with self.lock:
            return self._wait

    @property
    def sleep_time(self) -> _Optional[float]:
        if self.loop_sleep_time is None:
            return None
        sleep_time = self.loop_sleep_time - self.loop_delay
        if sleep_time < 0:
            return 0.0
        return sleep_time

    @property
    def args(self) -> tuple[tuple[_Any, ...]]:
        """
        Get the arguments of the thread.

        :rtype: tuple[tuple[_Any, ...]]
        :return: The arguments of the thread.
        """

        with self.lock:
            return getattr(self, "_args", ())

    @args.setter
    def args(self, value: tuple[_Any, ...]):
        """
        Set the arguments of the thread.

        :param value: The arguments of the thread.
        :rtype: None
        """

        with self.lock:
            setattr(self, "_args", value)

    @property
    def kwargs(self) -> dict[str, _Any]:
        """
        Get the keyword arguments of the thread.

        :rtype: dict[str, _Any]
        :return: The keyword arguments of the thread.
        """

        with self.lock:
            return getattr(self, "_kwargs", {})

    @kwargs.setter
    def kwargs(self, value: dict[str, _Any]):
        """
        Set the keyword arguments of the thread.

        :param value: The keyword arguments of the thread.
        :rtype: None
        """

        with self.lock:
            setattr(self, "_kwargs", value)

    @property
    def target(self) -> _Optional[_Callable[..., _Any]]:
        """
        Get the target of the thread.

        :rtype: Callable[..., _Any]
        :return: The target of the thread.
        """

        with self.lock:
            return getattr(self, "_target", None)

    @_contextmanager
    def ignore(self) -> None:
        """
        Context manager to ignore the stop.

        :rtype: None
        :return: Nothing
        """

        ignore_stop_before = self.ignore_stop
        self.ignore_stop = True
        yield
        self.ignore_stop = ignore_stop_before

    @_contextmanager
    def loop_wait(self, block: bool = True, timeout: _Optional[float] = None) -> None:
        """
        Context manager to wait for the next loop.

        :param block: Block before entering the context manager.
        :param timeout: Timeout for the block.
        :rtype: None
        :return: Nothing
        """

        loop_wait_before = self._wait
        with self.lock:
            self._wait = True
        if block:  # wait for next loop
            loop_started_at = self.loop_started_at
            if loop_started_at is not None:
                block_start_counter = _time.perf_counter()
                while loop_started_at != self.loop_started_at:
                    if timeout is not None:
                        if _time.perf_counter() - block_start_counter > timeout:
                            raise TimeoutError("Timeout while waiting for loop.")
                    _time.sleep(0.001)
        yield
        with self.lock:
            self._wait = loop_wait_before

    def start_watchdog(self) -> None:
        """
        Start the watchdog. If the watchdog is already running, nothing happens.

        :rtype: None
        :return: Nothing
        """

        if self._watchdog_target is None:
            return  # watchdog is disabled
        if self._watchdog_thread is not None:
            if self._watchdog_thread.is_alive():
                return  # watchdog is already running
        self._watchdog_thread = _threading.Thread(name=f"{self.name}.watchdog", target=self._watchdog_loop, daemon=True)
        self._watchdog_thread.start()

    def _watchdog_loop(self) -> None:
        """
        Watchdog of the thread.

        :rtype: None
        :return: Nothing
        """

        self.logger.debug(f"{self._cls_name} watchdog started.")

        while True:
            watchdog_loop_start_counter = _time.perf_counter()
            try:
                watchdog_target_result = bool(self._watchdog_target(self))
                if not watchdog_target_result:
                    self.logger.info(f"{self._cls_name} watchdog received stop signal.")
                    break
            except BaseException as e:
                handle_exception(msg=f"{self._cls_name} watchdog raised an exception", e=e, logger=self.logger, chain=False)
                self.raise_exception(ThreadWatchdogError)
            watchdog_loop_delay = _time.perf_counter() - watchdog_loop_start_counter
            if self.loop_sleep_time:
                sleep_start_counter = _time.perf_counter()
                while _time.perf_counter() - sleep_start_counter < self.loop_sleep_time - watchdog_loop_delay:
                    _time.sleep(0.001)


        self.logger.debug(f"{self._cls_name} watchdog ended.")

    def raise_exception(self, exception: _Union[type[BaseException], BaseException]) -> None:
        """
        Raises the given exception in the context of this thread.

        :param exception: The exception to raise.
        :rtype: None
        :return: Nothing
        """

        # check if the exception is an Exception type
        if isinstance(exception, BaseException):
            self._interrupt_exception = exception
            exception = ThreadInterrupt
        elif issubclass(exception, BaseException):
            self._interrupt_exception = None
        else:
            raise TypeError("Only types or object derived from BaseException can be raised")

        res = _ctypes.pythonapi.PyThreadState_SetAsyncExc(_ctypes.c_long(self.ident), _ctypes.py_object(exception))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # if it returns a number greater than one, you're in trouble, and you should call it again with exc=None to revert the effect
            _ctypes.pythonapi.PyThreadState_SetAsyncExc(_ctypes.c_long(self.ident), None)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    def stop(self) -> None:
        """
        Send a stop signal to the thread.

        :rtype: None
        :return: Nothing
        """

        self.raise_exception(ThreadStop)

    def kill(self) -> None:
        """
        Send a kill signal to the thread.

        :rtype: None
        :return: Nothing
        """

        self.raise_exception(ThreadKill)

    def run(self) -> None:
        """
        THe inner run method of the thread. Don't override this method. Use loop instead.

        :rtype: None
        :return: Nothing
        """

        self.on_start()

        with self.lock:
            self._started_at = _local_now()

        self.logger.info(f"{self._cls_name} started.")

        while True:
            # start watchdog
            self.start_watchdog()

            try:
                try:
                    # get loop start time
                    with self.lock:
                        self._loop_started_at = _local_now()
                    loop_start_counter = _time.perf_counter()

                    self.logger.debug(f"{self._cls_name} is running loop.")

                    # wait
                    if self.wait:
                        self.logger.debug(f"{self._cls_name} loop is waiting.")
                        while self.wait:
                            _time.sleep(0.001)
                        self.logger.debug(f"{self._cls_name} loop is continuing.")

                    # execute loop start
                    self.on_loop_start()

                    # execute loop
                    self.loop()

                    # execute loop end
                    self.on_loop_end()

                    with self.lock:
                        # set loop end time
                        self._loop_ended_at = _local_now()

                        # set loop delay
                        self._loop_delay = _time.perf_counter() - loop_start_counter

                    # sleep if necessary
                    if not self.loop_disabled:
                        if self.sleep_time:
                            self.logger.debug(f"{self._cls_name} loop is sleeping for {self.sleep_time} seconds.")
                            sleep_start_counter = _time.perf_counter()
                            while _time.perf_counter() - sleep_start_counter < self.sleep_time:
                                _time.sleep(0.001)
                except ThreadInterrupt:
                    if self._interrupt_exception is None:
                        raise RuntimeError("ThreadInterrupt was raised but no exception was set.")
                    else:
                        raise self._interrupt_exception
            except self._continue_exceptions as e:
                self.logger.debug(f"{self._cls_name} received {e.__class__.__name__}. Continue loop.")
                continue
            except self._stop_exceptions as e:
                if self.ignore_stop:
                    self.logger.debug(f"{self._cls_name} received {e.__class__.__name__} but ignore_stop is True. Continue loop.")
                    continue
                else:
                    self.logger.debug(f"{self._cls_name} received {e.__class__.__name__}. Stop loop.")
                    self.on_stop()
                    break
            except self._kill_exceptions as e:
                self.logger.debug(f"{self._cls_name} received {e.__class__.__name__}. Kill loop.")
                break
            except BaseException as e:
                if self._interrupt_exception is None:
                    handle_exception(msg=f"{self._cls_name} loop raised an exception", e=e, logger=self.logger, chain=True)
                else:
                    self._interrupt_exception = None
                    handle_exception(msg=f"{self._cls_name} loop raised an exception", e=e, logger=self.logger, chain=False)

                if self._loop_stop_on_other_exception:
                    break

        # execute end
        self.on_end()

        with self.lock:
            self._ended_at = _local_now()

        self.logger.info(f"{self._cls_name} ended.")

    def on_start(self) -> None:
        """
        Method to execute on start. This method is called before the loop starts by the run method.
        You can override this method.

        :rtype: None
        :return: Nothing
        """

        ...

    def on_loop_start(self) -> None:
        """
        Method to execute on loop start. This method is called every time the loop starts by the run method.
        You can override this method.

        :rtype: None
        :return: Nothing
        """

        ...

    def on_loop_end(self) -> None:
        """
        Method to execute on loop end. This method is called every time the loop ends by the run method.
        You can override this method.

        :rtype: None
        :return: Nothing
        """

        ...

    def on_stop(self) -> None:
        """
        Method to execute on stop. This method is called when the thread is stopped by the run method.
        You can override this method.

        :rtype: None
        :return: Nothing
        """

        ...

    def on_end(self) -> None:
        """
        Method to execute on end. This method is called when the thread stopped or killed by the run method.
        You can override this method.

        :rtype: None
        :return:
        """

        ...

    def loop(self) -> None:
        """
        The loop method. You can override this method.

        :rtype: None
        :return: Nothing
        """

        if self.target is None:
            return
        self.target(*self.args, **self.kwargs)


def handle_exception(msg: str, e: BaseException, logger: _logging.Logger, chain: bool = True) -> str:
    """
    Handle an exception.

    :param msg: The name of the exception.
    :param e: The exception.
    :param logger: The logger.
    :param chain: If the exception chain should be printed.
    :rtype: str
    :return: The exception message.
    """

    tb_str = "".join(_traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__, chain=chain)).strip()
    msg += f":\n{tb_str}"
    logger.error(msg)
    print(msg, file=_sys.stderr)
    return msg
