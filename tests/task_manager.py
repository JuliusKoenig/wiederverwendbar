import logging as _logging
import inspect as _inspect

import threading as _threading
import time as _time
from itertools import count as _count
from typing import Any as _Any, Optional as _Optional, Union as _Union
from datetime import datetime as _datetime, timedelta as _timedelta
from enum import Enum as _Enum

from bson import ObjectId as _ObjectId
from mongoengine import DoesNotExist as _DoesNotExist, ValidationError as _ValidationError, Document as _Document, EmbeddedDocument as _EmbeddedDocument, EnumField as _EnumField, \
    DateTimeField as _DateTimeField, \
    DictField as _DictField, StringField as _StringField, ReferenceField as _ReferenceField, FloatField as _FloatField, IntField as _IntField, \
    EmbeddedDocumentListField as _EmbeddedDocumentListField

from wiederverwendbar.functions.datetime import local_now as _local_now, to_local as _to_local
from wiederverwendbar.logger.helper import remove_logger as _remove_logger
from wiederverwendbar.logger.context import LoggingContext as _LoggingContext
from wiederverwendbar.logger.singleton import SubLogger as _SubLogger
from wiederverwendbar.mongoengine.logger.streamer import MongoengineLogStreamer as _MongoengineLogStreamer
from wiederverwendbar.mongoengine.logger.documets import MongoengineLogDocument as _MongoengineLogDocument
from wiederverwendbar.mongoengine.logger.handlers import MongoengineLogHandler as _MongoengineLogHandler
from wiederverwendbar.threading import ExtendedThread as _ExtendedThread, handle_exception as _handle_exception, ThreadLoopContinue as _ThreadLoopContinue, \
    ThreadStop as _ThreadStop

MODULE_NAME = "task_manager"
DEFAULT_LOG_LEVEL = _logging.INFO
MANAGER_NAMESPACE_NAME = f"{MODULE_NAME}.manager"
WORKER_NAMESPACE_NAME = f"{MODULE_NAME}.worker"
TASK_NAMESPACE_NAME = f"{MODULE_NAME}.task"


class WorkerSignalType(_Enum):
    STOP = "stop"
    CANCEL = "cancel"


class _WorkerSignal(_EmbeddedDocument):
    type: WorkerSignalType = _EnumField(WorkerSignalType, required=True)
    send_at: _datetime = _DateTimeField(required=True)
    content: dict[_Any, _Any] = _DictField()


class WorkerState(_Enum):
    BUSY = "busy"
    IDLE = "idle"
    QUIT = "quit"


class _WorkerDocument(_Document):
    meta = {"collection": WORKER_NAMESPACE_NAME}

    name: str = _StringField(required=True, unique_with="manager")
    manager: str = _StringField(required=True)
    state: WorkerState = _EnumField(WorkerState, required=True)
    started_at: _Optional[_datetime] = _DateTimeField()
    last_seen: _Optional[_datetime] = _DateTimeField()
    delay: _Optional[float] = _FloatField()
    current_task: _Optional["_TaskDocument"] = _ReferenceField("_TaskDocument")
    signals: list[_WorkerSignal] = _EmbeddedDocumentListField(_WorkerSignal)


class _WorkerLogDocument(_MongoengineLogDocument):
    meta = {"collection": f"{WORKER_NAMESPACE_NAME}.log",
            "indexes": ["owner"]}
    owner: _WorkerDocument = _ReferenceField(_WorkerDocument, required=True)


class TaskState(_Enum):
    NEW = "new"
    RUNNING = "running"  # running states
    CANCELED = "canceled"  # final states
    FINISHED = "finished"  # final states
    FAILED = "failed"  # final states

    @classmethod
    def waiting_states(cls) -> list["TaskState"]:
        return [cls.NEW]

    @classmethod
    def running_states(cls) -> list["TaskState"]:
        return [cls.RUNNING]

    @classmethod
    def failed_states(cls) -> list["TaskState"]:
        return [cls.CANCELED, cls.FAILED]

    @classmethod
    def final_states(cls) -> list["TaskState"]:
        return [cls.FINISHED] + cls.failed_states()


class _TaskCancelSignal(_ThreadLoopContinue):
    ...


class _TaskDocument(_Document):
    meta = {"collection": TASK_NAMESPACE_NAME}

    name: str = _StringField(required=True)
    manager: str = _StringField(required=True)
    state: TaskState = _EnumField(TaskState, required=True)
    worker: _Optional[_WorkerDocument] = _ReferenceField(_WorkerDocument)
    log_level: int = _IntField(required=True)
    created_at: _datetime = _DateTimeField(required=True)
    due_at: _datetime = _DateTimeField(required=True)
    started_at: _Optional[_datetime] = _DateTimeField()
    ended_at: _Optional[_datetime] = _DateTimeField()
    params: dict[str, _Any] = _DictField(required=True)
    result: _Optional[dict[str, _Any]] = _DictField()


class _TaskLogDocument(_MongoengineLogDocument):
    meta = {"collection": f"{TASK_NAMESPACE_NAME}.log",
            "indexes": ["owner"]}
    owner: _TaskDocument = _ReferenceField(_TaskDocument, required=True)


class _BaseProxy:
    proxy_document_cls: _Union[type[_WorkerDocument], type[_TaskDocument]] = None
    log_document_cls: _Union[type[_WorkerLogDocument], type[_WorkerLogDocument]] = None

    def __init__(self, object_id: _ObjectId = None):
        self._proxy_document: _Union[_WorkerDocument, _TaskDocument] = self.proxy_document_cls.objects.get(id=object_id)

    def __str__(self):
        return f"{self.__class__.__name__}(name={self.name}, manager={self.manager}, state={self.state})"

    @property
    def id(self) -> _ObjectId:
        return self._proxy_document.id

    @property
    def name(self) -> str:
        return self._proxy_document.name

    @property
    def manager(self) -> "Manager":
        return Manager.get_manager(self._proxy_document.manager)

    @property
    def state(self) -> _Union[WorkerState, TaskState]:
        self.reload()
        return self._proxy_document.state

    @property
    def started_at(self) -> _Optional[_datetime]:
        self.reload()
        return self._proxy_document.started_at

    def reload(self) -> None:
        self._proxy_document.reload()

    def log_streamer(self,
                     to: _Optional[callable] = None,
                     begin: _Optional[_datetime] = None,
                     log_stream_rate: _Optional[float] = None) -> _MongoengineLogStreamer:
        if begin is None:
            begin = self.started_at
        if log_stream_rate is None:
            log_stream_rate = self.manager.log_stream_rate
        return _MongoengineLogStreamer(log_document=self.log_document_cls,
                                       search={"owner": self._proxy_document},
                                       to=to,
                                       name=f"{self.name}.log_streamer",
                                       begin=begin,
                                       stream_rate=log_stream_rate)

    def wait_for_state(self, *states: _Union[WorkerState, TaskState], timeout: _Optional[float] = None) -> None:
        start_time = _time.perf_counter()
        while self.state not in states:
            if timeout is not None and _time.perf_counter() - start_time > timeout:
                raise TimeoutError(f"Timeout while waiting for task '{self.name}' to reach state '{states}'")
            _time.sleep(0.001)


class Worker(_BaseProxy):
    proxy_document_cls = _WorkerDocument
    log_document_cls = _WorkerLogDocument

    def __init__(self, object_id: _ObjectId = None):
        if object_id is None:
            stack = _inspect.stack()
            for frame_info in stack[1:]:
                for f_local_name, f_local in dict(frame_info.frame.f_locals).items():
                    if isinstance(f_local, _WorkerThread):
                        object_id = f_local.worker_document.id
                        break
                if object_id is not None:
                    break
            if object_id is None:
                raise ValueError("No worker found in stack")
        super().__init__(object_id=object_id)

    @property
    def state(self) -> WorkerState:
        return super().state

    @property
    def last_seen(self) -> _datetime:
        self.reload()
        return self._proxy_document.last_seen

    @property
    def delay(self) -> float:
        self.reload()
        return self._proxy_document.delay

    @property
    def current_task(self) -> _Optional["ScheduledTask"]:
        self.reload()
        if self._proxy_document.current_task is None:
            return None
        return ScheduledTask(object_id=self._proxy_document.current_task.id)

    def wait_for_state(self, *states: WorkerState, timeout: _Optional[float] = None) -> None:
        super().wait_for_state(*states, timeout=timeout)

    def wait_for_task(self, timeout: _Optional[float] = None) -> None:
        current_task = self.current_task
        if current_task is None:
            return
        current_task.wait_for_end(timeout=timeout)

    # def terminate(self, wait: bool = False, timeout: _Optional[float] = None) -> None:
    #     if self.state == WorkerState.TERMINATE:
    #         return
    #     elif self.state == WorkerState.QUIT:
    #         raise ValueError(f"Worker '{self.name}' is already quitting")
    #     self._proxy_document.state = WorkerState.TERMINATE
    #     self._proxy_document.save()
    #     if wait:
    #         self.wait_for_state(WorkerState.TERMINATE, timeout=timeout)


class ScheduledTask(_BaseProxy):
    proxy_document_cls = _TaskDocument
    log_document_cls = _TaskLogDocument

    def __init__(self, object_id: _ObjectId = None):
        if object_id is None:
            stack = _inspect.stack()
            for frame_info in stack[1:]:
                for f_local_name, f_local in dict(frame_info.frame.f_locals).items():
                    if isinstance(f_local, _WorkerThread):
                        object_id = f_local.current_task.id
                        break
                if object_id is not None:
                    break
            if object_id is None:
                raise ValueError("No task found in stack")
        super().__init__(object_id=object_id)

    @property
    def state(self) -> TaskState:
        return super().state

    @property
    def worker(self) -> _Optional[Worker]:
        self.reload()
        if self._proxy_document.worker is None:
            return None
        return Worker(object_id=self._proxy_document.worker.id)

    @property
    def created_at(self) -> _datetime:
        return self._proxy_document.created_at

    @property
    def due_at(self) -> _datetime:
        return self._proxy_document.due_at

    @property
    def ended_at(self) -> _Optional[_datetime]:
        self.reload()
        return self._proxy_document.ended_at

    @property
    def params(self) -> dict[str, _Any]:
        return self._proxy_document.params.copy()

    @property
    def result(self) -> _Optional[dict[str, _Any]]:
        self.reload()
        if self._proxy_document.result is None:
            return None
        return self._proxy_document.result.copy()

    @property
    def duration(self) -> _Optional[float]:
        self.reload()
        if self._proxy_document.started_at is None or self._proxy_document.ended_at is None:
            return None
        return (self._proxy_document.ended_at - self._proxy_document.started_at).total_seconds()

    @property
    def is_running(self) -> bool:
        return self.state in TaskState.running_states()

    def wait_for_state(self, *states: TaskState, timeout: _Optional[float] = None) -> None:
        super().wait_for_state(*states, timeout=timeout)

    def wait_for_end(self, timeout: _Optional[float] = None) -> None:
        self.wait_for_state(*TaskState.final_states(), timeout=timeout)

    # def cancel(self, wait: bool = False, timeout: _Optional[float] = None) -> None:
    #     self.reload()
    #     if self._proxy_document.state == TaskState.CANCELING:
    #         return
    #     if self._proxy_document.state == TaskState.CANCELED:
    #         raise ValueError(f"Task '{self.name}' is already canceled")
    #     elif self._proxy_document.state == TaskState.FINISHED:
    #         raise ValueError(f"Task '{self.name}' is already finished")
    #     elif self._proxy_document.state == TaskState.FAILED:
    #         raise ValueError(f"Task '{self.name}' is already failed")
    #
    #     self._proxy_document.state = TaskState.CANCELING
    #     self._proxy_document.save()
    #
    #     if wait:
    #         self.wait_for_state(TaskState.CANCELED, timeout=timeout)


_worker_counter = _count().__next__
_worker_counter()  # skip 0


class _WorkerThread(_ExtendedThread):
    def __init__(self,
                 name: str,
                 manager: "Manager",
                 document: _WorkerDocument,
                 log_level: int,
                 log_push_rate: _Optional[float] = None,
                 log_push_max_entries: _Optional[int] = None,
                 task_ignore_loggers_equal: _Optional[list[str]] = None,
                 task_ignore_loggers_like: _Optional[list[str]] = None,
                 logger: _Optional[_logging.Logger] = None,
                 loop_sleep_time: _Optional[float] = None):

        self._manager: "Manager" = manager

        # define document attributes
        self._state: WorkerState = WorkerState.BUSY
        self._last_seen: _datetime = _local_now()
        self._current_task: _Optional[_TaskDocument] = None

        # define worker attributes
        self._log_level: int = log_level
        self._logger_handler: _Optional[_MongoengineLogHandler] = None
        self._worker_document: _WorkerDocument = document
        self._log_push_rate: _Optional[float] = log_push_rate
        self._log_push_max_entries: _Optional[int] = log_push_max_entries
        self._task_logger: _Optional[_logging.Logger] = None
        self._task_logger_handler: _Optional[_MongoengineLogHandler] = None
        if task_ignore_loggers_equal is None:
            task_ignore_loggers_equal = []
        self._task_ignore_loggers_equal: list[str] = task_ignore_loggers_equal
        if task_ignore_loggers_like is None:
            task_ignore_loggers_like = []
        self._task_ignore_loggers_like: list[str] = task_ignore_loggers_like
        self._task_result: _Optional[dict[str, _Any]] = None
        self._task_state: _Optional[TaskState] = None

        super().__init__(name=name,
                         cls_name=name,
                         logger=logger,
                         loop_sleep_time=loop_sleep_time,
                         loop_stop_on_other_exception=False,
                         watchdog_target=self._watchdog_target)

    # --- threads ---

    @classmethod
    def _watchdog_target(cls, thread) -> bool:
        thread: _WorkerThread

        # check if manager thread is alive
        if not thread.manager_thread.is_alive():
            thread.stop()
            return False

        # check if worker signal
        thread.worker_document.reload()
        for signal in thread.worker_document.signals:
            print(signal)

        return True

    # --- properties ---

    @property
    def worker_document(self) -> _WorkerDocument:
        with self.lock:
            return self._worker_document

    @property
    def state(self) -> WorkerState:
        with self.lock:
            return self._state

    @state.setter
    def state(self, value: WorkerState) -> None:
        with self.lock:
            if value == self._state:
                return
            self._logger.debug(f"Worker state changed from '{self._state}' to '{value}'")
            self._state = value
            self._worker_document.state = self._state
            self._worker_document.save()

    @property
    def last_seen(self) -> _datetime:
        with self.lock:
            return self._last_seen

    @last_seen.setter
    def last_seen(self, value: _datetime) -> None:
        with self.lock:
            self._last_seen = value
            self._worker_document.last_seen = self._last_seen
            self._worker_document.save()

    @property
    def current_task(self) -> _Optional[_TaskDocument]:
        with self.lock:
            return self._current_task

    @current_task.setter
    def current_task(self, value: _Optional[_TaskDocument]) -> None:
        with self.lock:
            self._current_task = value
            self._worker_document.current_task = self._current_task
            self._worker_document.save()

    @property
    def log_push_rate(self) -> float:
        with self.lock:
            if self._log_push_rate is None:
                return self._manager.log_push_rate
            return self._log_push_rate

    @log_push_rate.setter
    def log_push_rate(self, value: float) -> None:
        with self.lock:
            self._log_push_rate = value

    @property
    def log_push_max_entries(self) -> int:
        with self.lock:
            if self._log_push_max_entries is None:
                return self._manager.log_push_max_entries
            return self._log_push_max_entries

    @log_push_max_entries.setter
    def log_push_max_entries(self, value: int) -> None:
        with self.lock:
            self._log_push_max_entries = value

    @property
    def loop_sleep_time(self) -> _Optional[float]:
        with self.lock:
            if self._loop_sleep_time is None:
                return self._manager.worker_loop_sleep_time
        return super().loop_sleep_time

    @property
    def manager_thread(self):
        return self._manager.thread

    @property
    def task_ignore_loggers_equal(self) -> list[str]:
        task_ignore_loggers_equal = self._manager.task_ignore_loggers_equal.copy()
        with self.lock:
            task_ignore_loggers_equal.extend(self._task_ignore_loggers_equal)
            return task_ignore_loggers_equal

    @task_ignore_loggers_equal.setter
    def task_ignore_loggers_equal(self, value: list[str]):
        with self.lock:
            self._task_ignore_loggers_equal = value

    @property
    def task_ignore_loggers_like(self) -> list[str]:
        task_ignore_loggers_like = self._manager.task_ignore_loggers_like.copy()
        with self.lock:
            task_ignore_loggers_like.extend(self._task_ignore_loggers_like)
            if "pymongo" not in task_ignore_loggers_like:
                task_ignore_loggers_like.append("pymongo")
            return task_ignore_loggers_like

    @task_ignore_loggers_like.setter
    def task_ignore_loggers_like(self, value: list[str]):
        with self.lock:
            self._task_ignore_loggers_like = value

    # --- methods ---

    def on_start(self) -> None:
        # create worker logger handler
        self._logger_handler = _MongoengineLogHandler(document=_WorkerLogDocument,
                                                      document_kwargs={"owner": self.worker_document},
                                                      buffer_size=self._manager.log_push_max_entries,
                                                      buffer_periodical_flush_timing=self._manager.log_push_rate)

        # configure logger
        if not isinstance(self._logger, _SubLogger):
            self._logger.setLevel(self._log_level)
            self._logger.addHandler(self._logger_handler)
        else:
            with self._logger.reconfigure():
                self._logger.setLevel(self._log_level)
                self._logger.addHandler(self._logger_handler)

        # set all running tasks for this worker to failed

        for running_task in _TaskDocument.objects(worker=self.worker_document,
                                                  state__in=TaskState.running_states()):
            self.logger.debug(f"Setting task '{running_task.name}' to state '{TaskState.CANCELED}'")

            # set task attributes
            running_task.state = TaskState.CANCELED
            running_task.ended_at = _local_now()
            running_task.result = {"error": "Worker restarted"}

            # save task
            running_task.save()
        with self.lock:
            self._started_at = _local_now()
            self._worker_document.started_at = self._started_at
            self._worker_document.save()

    def on_loop_start(self) -> None:
        # set state to idle
        self.state = WorkerState.IDLE

        with self.lock:
            # set last seen and delay
            self._worker_document.last_seen = _local_now()
            self._worker_document.delay = self._loop_delay
            self._worker_document.save()

    def loop(self) -> None:
        # get next due task
        self.current_task: _TaskDocument = _TaskDocument.objects(manager=self._manager.name,
                                                                 due_at__lte=_local_now(),
                                                                 state=TaskState.NEW,
                                                                 worker=None).order_by("due_at").first()
        if self.current_task is not None:
            self.on_task_start()

            # run task
            raise_at_end = None
            try:
                self.task()
            except (_ThreadLoopContinue, _ThreadStop) as e:
                if isinstance(e, _ThreadStop):
                    self._task_result = {"error": "Worker stopped"}
                elif isinstance(e, _ThreadLoopContinue):
                    self._task_result = {"error": "Worker continued"}
                self._task_state = TaskState.CANCELED
                raise_at_end = e
            except Exception as e:
                self._task_result = {"error": str(e)}
                self._task_state = TaskState.FAILED
                _handle_exception(msg=f"Error while running task '{self.current_task.name}'", e=e, logger=self._logger)

            self.on_task_end()

            # set current task to None
            self.current_task = None

            if raise_at_end is not None:
                raise raise_at_end

    def on_task_start(self) -> None:
        # start task
        self.current_task.state = TaskState.RUNNING
        self.current_task.worker = self.worker_document
        self.current_task.started_at = _local_now()
        self.current_task.save()

        # set state to busy
        self.state = WorkerState.BUSY

        self._logger.info(f"Running task '{self.current_task.name}'")

        # create logger
        self._task_logger = _logging.getLogger(f"{TASK_NAMESPACE_NAME}.{self.current_task.name}")

        # add logger handler
        self._task_logger_handler = _MongoengineLogHandler(document=_TaskLogDocument,
                                                           document_kwargs={"owner": self.current_task},
                                                           buffer_size=self.log_push_max_entries,
                                                           buffer_periodical_flush_timing=self.log_push_rate)
        if not isinstance(self._task_logger, _SubLogger):
            self._task_logger.setLevel(self.current_task.log_level)
            self._task_logger.addHandler(self._task_logger_handler)
        else:
            with self._task_logger.reconfigure():
                self._task_logger.setLevel(self.current_task.log_level)
                self._task_logger.addHandler(self._task_logger_handler)

        self._task_result = None
        self._task_state = None

    def task(self):
        with _LoggingContext(context_logger=self._task_logger,
                             ignore_loggers_equal=self.task_ignore_loggers_equal,
                             ignore_loggers_like=self.task_ignore_loggers_like):
            task_func = self._manager.get_task_func(self.current_task.name)
            self._task_result = task_func(**self.current_task.params)
            self._task_state = TaskState.FINISHED

    def on_task_end(self) -> None:
        # close logger handler and remove it
        self._task_logger_handler.close()
        if not isinstance(self._task_logger, _SubLogger):
            self._task_logger.removeHandler(self._task_logger_handler)
        else:
            with self._task_logger.reconfigure():
                self._task_logger.removeHandler(self._task_logger_handler)

        # remove logger
        _remove_logger(self._task_logger)

        self._logger.info(f"Finishing task '{self.current_task.name}'")

        try:
            # set task attributes
            self.current_task.state = self._task_state
            self.current_task.ended_at = _local_now()
            self.current_task.result = self._task_result

            # save task
            self.current_task.save()
        except _ValidationError as e:
            self.current_task.state = TaskState.FAILED
            self.current_task.result = {"error": _handle_exception(msg=f"Validation error while saving task '{self.current_task.name}'", e=e, logger=self._logger)}
            self.current_task.save()

    def on_loop_end(self) -> None:
        ...

    def on_stop(self) -> None:
        # set state to quit
        self.state = WorkerState.QUIT

    def on_end(self) -> None:
        # close logger handler and remove it
        self._logger_handler.close()
        if not isinstance(self._logger, _SubLogger):
            self._logger.removeHandler(self._logger_handler)
        else:
            with self._logger.reconfigure():
                self._logger.removeHandler(self._logger_handler)

        # remove logger
        _remove_logger(self._logger)


class Manager:
    _manager_lock = _threading.Lock()
    managers: dict[str, "Manager"] = {}

    def __init__(self,
                 name: _Optional[str] = None,
                 log_level: _Optional[int] = None,
                 log_stream_rate: _Optional[float] = None,
                 log_push_rate: _Optional[float] = None,
                 log_push_max_entries: _Optional[int] = None,
                 minimum_last_seen_time_for_other_worker: _Optional[int] = None,
                 worker_loop_sleep_time: _Optional[float] = None,
                 task_ignore_loggers_equal: _Optional[list[str]] = None,
                 task_ignore_loggers_like: _Optional[list[str]] = None, ):
        self._lock = _threading.Lock()

        if name is None:
            name = "default"
        self._name: str = name

        self._logger = _logging.getLogger(f"{MANAGER_NAMESPACE_NAME}.{self.name}")
        if log_level is None:
            if self._logger.level == _logging.NOTSET:
                log_level = DEFAULT_LOG_LEVEL
            else:
                log_level = self._logger.level
        if not isinstance(self._logger, _SubLogger):
            self._logger.setLevel(log_level)
        else:
            with self._logger.reconfigure():
                self._logger.setLevel(log_level)

        if log_stream_rate is None:
            log_stream_rate = 0.001
        self._log_stream_rate: float = log_stream_rate

        if log_push_rate is None:
            log_push_rate = 1.0
        self._log_push_rate: float = log_push_rate

        if log_push_max_entries is None:
            log_push_max_entries = 10
        self._log_push_max_entries: int = log_push_max_entries

        if minimum_last_seen_time_for_other_worker is None:
            minimum_last_seen_time_for_other_worker = 10
        self._minimum_last_seen_time_for_other_worker: int = minimum_last_seen_time_for_other_worker

        self._workers: dict[str, _ObjectId] = {}

        if worker_loop_sleep_time is None:
            worker_loop_sleep_time = 1
        self._worker_loop_sleep_time: float = worker_loop_sleep_time

        if task_ignore_loggers_equal is None:
            task_ignore_loggers_equal = []
        self._task_ignore_loggers_equal: list[str] = task_ignore_loggers_equal
        if task_ignore_loggers_like is None:
            task_ignore_loggers_like = []
        self._task_ignore_loggers_like: list[str] = task_ignore_loggers_like

        self._thread = _threading.current_thread()

        self._registered_tasks: dict[str, callable] = {}

        self._registered_tasks_param: dict[str, dict[str, type]] = {}

        self._registered_tasks_param_defaults: dict[str, dict[str, _Any]] = {}

        # add manager to managers
        with self._manager_lock:
            if self.name in self.managers:
                raise ValueError(f"Manager with name '{self.name}' already exists")
            self.managers[self.name] = self

        self._logger.info("Manager created")

    @classmethod
    def get_manager(cls, name: str) -> "Manager":
        with cls._manager_lock:
            if name not in cls.managers:
                raise ValueError(f"No manager with name '{name}' found")
            return cls.managers[name]

    @property
    def name(self) -> str:
        with self._lock:
            return self._name

    @property
    def log_level(self) -> int:
        return self._logger.level

    @log_level.setter
    def log_level(self, value: int) -> None:
        self._logger.setLevel(value)

    @property
    def log_stream_rate(self) -> float:
        with self._lock:
            return self._log_stream_rate

    @log_stream_rate.setter
    def log_stream_rate(self, value: float) -> None:
        with self._lock:
            self._log_stream_rate = value

    @property
    def log_push_rate(self) -> float:
        with self._lock:
            return self._log_push_rate

    @log_push_rate.setter
    def log_push_rate(self, value: float) -> None:
        with self._lock:
            self._log_push_rate = value

    @property
    def log_push_max_entries(self) -> int:
        with self._lock:
            return self._log_push_max_entries

    @log_push_max_entries.setter
    def log_push_max_entries(self, value: int) -> None:
        with self._lock:
            self._log_push_max_entries = value

    @property
    def thread(self) -> _threading.Thread:
        with self._lock:
            return self._thread

    # --- worker management ---

    @property
    def minimum_last_seen_time_for_other_worker(self) -> _Optional[int]:
        with self._lock:
            return self._minimum_last_seen_time_for_other_worker

    @minimum_last_seen_time_for_other_worker.setter
    def minimum_last_seen_time_for_other_worker(self, value: _Optional[int]) -> None:
        with self._lock:
            self._minimum_last_seen_time_for_other_worker = value

    @property
    def worker_loop_sleep_time(self) -> float:
        with self._lock:
            return self._worker_loop_sleep_time

    @worker_loop_sleep_time.setter
    def worker_loop_sleep_time(self, value: float) -> None:
        with self._lock:
            self._worker_loop_sleep_time = value

    @property
    def worker_count(self) -> int:
        with self._lock:
            return len(self._workers)

    @property
    def worker_names(self) -> list[str]:
        with self._lock:
            return list(self._workers.keys())

    @property
    def workers(self) -> list[Worker]:
        with self._lock:
            return [Worker(object_id=worker_id) for worker_id in self._workers.values()]

    def create_worker(self,
                      name: _Optional[str] = None,
                      log_level: _Optional[int] = None,
                      log_push_rate: _Optional[float] = None,
                      log_push_max_entries: _Optional[int] = None,
                      loop_sleep_time: _Optional[float] = None,
                      task_ignore_loggers_equal: _Optional[list[str]] = None,
                      task_ignore_loggers_like: _Optional[list[str]] = None) -> Worker:
        self._logger.info(f"Creating worker '{name}'")

        worker_count = _worker_counter()

        if name is None:
            name = f"worker-{worker_count}"
        base_name = f"{WORKER_NAMESPACE_NAME}.{self.name}"
        if not name.startswith(base_name):
            name = f"{base_name}.{name}"

        if name in self.worker_names:
            raise ValueError(f"Worker with name '{name}' already exists")

        if log_level is None:
            log_level = self._logger.level

        # get worker document or create it
        try:
            worker_document = _WorkerDocument.objects.get(name=name,
                                                          manager=self.name)
            # check if other worker is running on this document
            if worker_document.state != WorkerState.QUIT:
                last_seen = _to_local(worker_document.last_seen)
                last_seen_delta_for_other_worker = _local_now() - last_seen
                if last_seen_delta_for_other_worker < _timedelta(seconds=self.minimum_last_seen_time_for_other_worker):
                    raise ValueError(f"Worker '{self.name}' already exists and was last seen {last_seen_delta_for_other_worker.total_seconds()} ago")
            worker_document.state = WorkerState.QUIT
            worker_document.started_at = None
            worker_document.last_seen = None
            worker_document.delay = None
            worker_document.current_task = None
            worker_document.signals = []
        except _DoesNotExist:
            worker_document = _WorkerDocument(name=name,
                                              manager=self.name,
                                              state=WorkerState.QUIT)
        worker_document.save()

        # create worker
        _WorkerThread(name=name,
                      manager=self,
                      document=worker_document,
                      log_level=log_level,
                      log_push_rate=log_push_rate,
                      log_push_max_entries=log_push_max_entries,
                      loop_sleep_time=loop_sleep_time,
                      task_ignore_loggers_equal=task_ignore_loggers_equal,
                      task_ignore_loggers_like=task_ignore_loggers_like)

        with self._lock:
            # add worker name and id to workers
            self._workers[name] = worker_document.id

        return Worker(object_id=worker_document.id)

    # --- task management ---

    @property
    def registered_tasks(self) -> list[str]:
        with self._lock:
            return list(self._registered_tasks.keys())

    @property
    def task_ignore_loggers_equal(self) -> list[str]:
        with self._lock:
            return self._task_ignore_loggers_equal.copy()

    @task_ignore_loggers_equal.setter
    def task_ignore_loggers_equal(self, value: list[str]):
        with self._lock:
            self._task_ignore_loggers_equal = value

    @property
    def task_ignore_loggers_like(self) -> list[str]:
        with self._lock:
            return self._task_ignore_loggers_like.copy()

    @task_ignore_loggers_like.setter
    def task_ignore_loggers_like(self, value: list[str]):
        with self._lock:
            self._task_ignore_loggers_like = value

    def get_task_func(self, name: str) -> callable:
        with self._lock:
            if name not in self._registered_tasks:
                raise ValueError(f"No task function with name '{name}' found")
            return self._registered_tasks[name]

    def registering_task(self, name: _Optional[str] = None, func: callable = None) -> callable:
        if self.worker_count > 0:
            raise RuntimeError("Cannot register tasks after workers are created")
        if not callable(func):
            raise ValueError(f"Argument 'func' must be a callable not '{type(func)}'")
        with self._lock:
            # get name from function if not provided
            if name is None:
                name = func.__name__

            self._logger.info(f"Registering task '{name}'")

            # check if task with name already registered
            if name in self._registered_tasks:
                raise ValueError(f"Task with name '{name}' already registered")

            # register task
            self._registered_tasks[name] = func
            self._registered_tasks_param[name] = {}
            self._registered_tasks_param_defaults[name] = {}

            # get signature from function
            func_params = dict(_inspect.signature(func).parameters)
            for param_name, param in func_params.items():
                self._registered_tasks_param[name][param_name] = param.annotation
                if param.default != _inspect.Parameter.empty:
                    self._registered_tasks_param_defaults[name][param_name] = param.default

            return func

    def register_task(self, name: _Optional[str] = None):
        def decorator(func: callable = None):
            return self.registering_task(name=name, func=func)

        return decorator

    def schedule_task(self, name: str, due: _Optional[_datetime] = None, log_level: _Optional[int] = None, **given_task_params) -> ScheduledTask:
        self._logger.info(f"Scheduling task '{name}'")

        if log_level is None:
            log_level = self._logger.level

        _ = self.get_task_func(name)
        if name not in self._registered_tasks_param:
            raise ValueError(f"No task parameters with name '{name}' found")
        task_params = self._registered_tasks_param[name]
        if name not in self._registered_tasks_param_defaults:
            raise ValueError(f"No task parameter defaults with name '{name}' found")
        task_param_defaults = self._registered_tasks_param_defaults[name]

        # check if all required parameters are provided
        for param_name, param_type in task_params.items():
            if param_name not in given_task_params:
                if param_name not in task_param_defaults:
                    raise ValueError(f"Parameter '{param_name}' is required for task '{name}'")
                try:
                    given_task_params[param_name] = task_param_defaults[param_name].copy()
                except AttributeError:
                    given_task_params[param_name] = task_param_defaults[param_name]

        # check if all provided parameters are correct
        for param_name, param_value in given_task_params.items():
            if not isinstance(param_value, task_params[param_name]):
                raise ValueError(f"Parameter '{param_name}' for task '{name}' must be of type '{task_params[param_name]}'")

        # create new task
        task = _TaskDocument(
            name=name,
            manager=self.name,
            state=TaskState.NEW,
            log_level=log_level,
            created_at=_local_now(),
            due_at=due or _local_now(),
            params=given_task_params
        )
        task.save()

        return ScheduledTask(object_id=task.id)
