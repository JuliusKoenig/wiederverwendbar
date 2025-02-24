import ctypes
import logging
import sys
import threading
import time
import traceback
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Any, Union

from wiederverwendbar.default import Default
from wiederverwendbar.functions.datetime import local_now


class ThreadInterrupt(threading.ThreadError):
    """
    Exception to interrupt a thread.
    """

    ...


class ThreadLoopContinue(threading.ThreadError):
    """
    Exception to continue a loop in a thread.
    """

    ...


class ThreadStop(threading.ThreadError):
    """
    Exception to stop a thread.
    """

    ...


class ThreadKill(threading.ThreadError):
    """
    Exception to kill a thread.
    """

    ...


class ThreadWatchdogError(threading.ThreadError):
    """
    Exception to indicate an error in the watchdog of a thread.
    """

    ...


class ExtendedThread(threading.Thread):
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
                 target: Union[Callable[..., Any], None, Default] = Default(),
                 name: Union[str, Default] = Default(),
                 args: Union[tuple[Any, ...], Default] = Default(),
                 kwargs: Union[dict[str, Any], Default] = Default(),
                 *,
                 daemon: Union[bool, None, Default] = Default(),
                 cls_name: Union[str, Default] = Default(),
                 logger: Union[logging.Logger, Default] = Default(),
                 ignore_stop: Union[bool, Default] = Default(),
                 loop_disabled: Union[bool, Default] = Default(),
                 loop_sleep_time: Union[float, None, Default] = Default(),
                 loop_stop_on_other_exception: Union[bool, Default] = Default(),
                 continue_exceptions: Union[list[type[BaseException]], Default] = Default(),
                 stop_exceptions: Union[list[type[BaseException]], Default] = Default(),
                 kill_exceptions: Union[list[type[BaseException]], Default] = Default(),
                 watchdog_target: Union[Callable[["ExtendedThread"], bool], None, Default] = Default(),
                 auto_start: Union[bool, Default] = Default()):
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

        if type(target) is Default:
            target = None

        if type(name) is Default:
            name = getattr(threading, "_newname")(f"{self.__class__.__name__}-%d")
            if target is not None:
                try:
                    target_name = target.__name__
                    name += f" ({target_name})"
                except AttributeError:
                    pass

        if type(args) is Default:
            args = ()

        if type(kwargs) is Default:
            kwargs = {}

        if type(daemon) is Default:
            daemon = None

        super().__init__(
            group=group,
            target=target,
            name=name,
            args=args,
            kwargs=kwargs,
            daemon=daemon
        )
        self.lock = threading.Lock()

        # set class name
        if type(cls_name) is Default:
            cls_name = self.__class__.__name__
        self._cls_name: str = cls_name

        # set logger
        if type(logger) is Default:
            # create a logger if none is provided
            logger = logging.getLogger(self.name)
        self._logger: logging.Logger = logger

        # set ignore stop
        if type(ignore_stop) is Default:
            ignore_stop = False
        self._ignore_stop: bool = ignore_stop

        # set loop disabled
        if type(loop_disabled) is Default:
            loop_disabled = False
        self._loop_disabled: bool = loop_disabled

        # set loop delay
        if type(loop_sleep_time) is Default:
            loop_sleep_time = None
        self._loop_sleep_time: Optional[float] = loop_sleep_time

        # set loop stop on other exception
        if type(loop_stop_on_other_exception) is Default:
            loop_stop_on_other_exception = False
        self._loop_stop_on_other_exception: bool = loop_stop_on_other_exception

        # set continue exceptions
        if type(continue_exceptions) is Default:
            continue_exceptions = []
        if ThreadLoopContinue not in continue_exceptions:
            continue_exceptions.append(ThreadLoopContinue)
        self._continue_exceptions: tuple[type[BaseException]] = tuple(continue_exceptions)

        # set stop exceptions
        if type(stop_exceptions) is Default:
            stop_exceptions = []
        if ThreadStop not in stop_exceptions:
            stop_exceptions.append(ThreadStop)
        self._stop_exceptions: tuple[type[BaseException]] = tuple(stop_exceptions)

        # set kill exceptions
        if type(kill_exceptions) is Default:
            kill_exceptions = []
        if ThreadKill not in kill_exceptions:
            kill_exceptions.append(ThreadKill)
        self._kill_exceptions: tuple[type[BaseException]] = tuple(kill_exceptions)

        # set watchdog target
        if type(watchdog_target) is Default:
            watchdog_target = None
        self._watchdog_target: Optional[Callable[[Union["ExtendedThread", Any]], bool]] = watchdog_target

        # set auto start
        if type(auto_start) is Default:
            auto_start = True
        self._auto_start: bool = auto_start

        # set internal variables
        self._started_at: Optional[datetime] = None
        self._ended_at: Optional[datetime] = None
        self._loop_started_at: Optional[datetime] = None
        self._loop_ended_at: Optional[datetime] = None
        self._loop_delay: float = 0.0
        self._wait: bool = False
        self._interrupt_exception: Optional[BaseException] = None
        self._watchdog_thread: Optional[threading.Thread] = None

        if self._auto_start:
            self.start()

    def __del__(self):
        if self.is_alive():
            self.stop()

    @property
    def logger(self) -> logging.Logger:
        """
        Get the logger of the thread.

        :rtype: logging.Logger
        :return: The logger of the thread.
        """

        with self.lock:
            return self._logger

    @logger.setter
    def logger(self, value: logging.Logger):
        """
        Set the logger of the thread.

        :param value: The new logger.
        :rtype: None
        """

        with self.lock:
            self._logger = value

    @property
    def started_at(self) -> Optional[datetime]:
        """
        Get the time when the thread was started.

        :rtype: datetime.datetime
        :return: The time when the thread was started.
        """

        with self.lock:
            return self._started_at

    @property
    def loop_started_at(self) -> Optional[datetime]:
        """
        Get the time when the loop was started.

        :rtype: datetime.datetime
        :return: The time when the loop was started.
        """

        with self.lock:
            return self._loop_started_at

    @property
    def loop_ended_at(self) -> Optional[datetime]:
        """
        Get the time when the loop was ended.

        :rtype: datetime.datetime
        :return: The time when the loop was ended.
        """

        with self.lock:
            return self._loop_ended_at

    @property
    def ended_at(self) -> Optional[datetime]:
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
    def loop_sleep_time(self) -> Optional[float]:
        """
        Get the loop sleep time.

        :rtype: float
        :return: The loop sleep time.
        """

        with self.lock:
            return self._loop_sleep_time

    @loop_sleep_time.setter
    def loop_sleep_time(self, value: Optional[float]):
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
    def sleep_time(self) -> Optional[float]:
        if self.loop_sleep_time is None:
            return None
        sleep_time = self.loop_sleep_time - self.loop_delay
        if sleep_time < 0:
            return 0.0
        return sleep_time

    @property
    def args(self) -> tuple[tuple[Any, ...]]:
        """
        Get the arguments of the thread.

        :rtype: tuple[tuple[Any, ...]]
        :return: The arguments of the thread.
        """

        with self.lock:
            return getattr(self, "_args", ())

    @args.setter
    def args(self, value: tuple[Any, ...]):
        """
        Set the arguments of the thread.

        :param value: The arguments of the thread.
        :rtype: None
        """

        with self.lock:
            setattr(self, "_args", value)

    @property
    def kwargs(self) -> dict[str, Any]:
        """
        Get the keyword arguments of the thread.

        :rtype: dict[str, Any]
        :return: The keyword arguments of the thread.
        """

        with self.lock:
            return getattr(self, "_kwargs", {})

    @kwargs.setter
    def kwargs(self, value: dict[str, Any]):
        """
        Set the keyword arguments of the thread.

        :param value: The keyword arguments of the thread.
        :rtype: None
        """

        with self.lock:
            setattr(self, "_kwargs", value)

    @property
    def target(self) -> Optional[Callable[..., Any]]:
        """
        Get the target of the thread.

        :rtype: Callable[..., _Any]
        :return: The target of the thread.
        """

        with self.lock:
            return getattr(self, "_target", None)

    @contextmanager
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

    @contextmanager
    def loop_wait(self, block: bool = True, timeout: Optional[float] = None) -> None:
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
                block_start_counter = time.perf_counter()
                while loop_started_at != self.loop_started_at:
                    if timeout is not None:
                        if time.perf_counter() - block_start_counter > timeout:
                            raise TimeoutError("Timeout while waiting for loop.")
                    time.sleep(0.001)
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
        self._watchdog_thread = threading.Thread(name=f"{self.name}.watchdog", target=self._watchdog_loop, daemon=True)
        self._watchdog_thread.start()

    def _watchdog_loop(self) -> None:
        """
        Watchdog of the thread.

        :rtype: None
        :return: Nothing
        """

        self.logger.debug(f"{self._cls_name} watchdog started.")

        while True:
            watchdog_loop_start_counter = time.perf_counter()
            try:
                watchdog_target_result = bool(self._watchdog_target(self))
                if not watchdog_target_result:
                    self.logger.info(f"{self._cls_name} watchdog received stop signal.")
                    break
            except BaseException as e:
                handle_exception(msg=f"{self._cls_name} watchdog raised an exception", e=e, logger=self.logger, chain=False)
                self.raise_exception(ThreadWatchdogError)
            watchdog_loop_delay = time.perf_counter() - watchdog_loop_start_counter
            if self.loop_sleep_time:
                sleep_start_counter = time.perf_counter()
                while time.perf_counter() - sleep_start_counter < self.loop_sleep_time - watchdog_loop_delay:
                    time.sleep(0.001)


        self.logger.debug(f"{self._cls_name} watchdog ended.")

    def raise_exception(self, exception: Union[type[BaseException], BaseException]) -> None:
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

        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self.ident), ctypes.py_object(exception))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # if it returns a number greater than one, you're in trouble, and you should call it again with exc=None to revert the effect
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self.ident), None)
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
            self._started_at = local_now()

        self.logger.info(f"{self._cls_name} started.")

        while True:
            # start watchdog
            self.start_watchdog()

            try:
                try:
                    # get loop start time
                    with self.lock:
                        self._loop_started_at = local_now()
                    loop_start_counter = time.perf_counter()

                    self.logger.debug(f"{self._cls_name} is running loop.")

                    # wait
                    if self.wait:
                        self.logger.debug(f"{self._cls_name} loop is waiting.")
                        while self.wait:
                            time.sleep(0.001)
                        self.logger.debug(f"{self._cls_name} loop is continuing.")

                    # execute loop start
                    self.on_loop_start()

                    # execute loop
                    self.loop()

                    # execute loop end
                    self.on_loop_end()

                    with self.lock:
                        # set loop end time
                        self._loop_ended_at = local_now()

                        # set loop delay
                        self._loop_delay = time.perf_counter() - loop_start_counter

                    # sleep if necessary
                    if not self.loop_disabled:
                        if self.sleep_time:
                            self.logger.debug(f"{self._cls_name} loop is sleeping for {self.sleep_time} seconds.")
                            sleep_start_counter = time.perf_counter()
                            while time.perf_counter() - sleep_start_counter < self.sleep_time:
                                time.sleep(0.001)
                    else:
                        break
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
            self._ended_at = local_now()

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


def handle_exception(msg: str, e: BaseException, logger: logging.Logger, chain: bool = True) -> str:
    """
    Handle an exception.

    :param msg: The name of the exception.
    :param e: The exception.
    :param logger: The logger.
    :param chain: If the exception chain should be printed.
    :rtype: str
    :return: The exception message.
    """

    tb_str = "".join(traceback.format_exception(type(e), value=e, tb=e.__traceback__, chain=chain)).strip()
    msg += f":\n{tb_str}"
    logger.error(msg)
    print(msg, file=sys.stderr)
    return msg
