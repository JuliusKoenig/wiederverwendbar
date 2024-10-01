import logging
import inspect
import threading
import time
from typing import Any, Optional, Union
from datetime import datetime
from enum import Enum

from bson import ObjectId
from mongoengine import Document, DoesNotExist, ValidationError, EnumField, DateTimeField, DictField, StringField, ReferenceField, FloatField

from wiederverwendbar.functions.datetime import local_now
from wiederverwendbar.logger.context import LoggingContext
from wiederverwendbar.logger.singleton import SubLogger
from wiederverwendbar.mongoengine.logger.documets import MongoengineLogDocument
from wiederverwendbar.mongoengine.logger.handlers import MongoengineLogHandler

MODULE_NAME = "task_manager"

# create module logger
LOGGER = logging.getLogger(MODULE_NAME)
MANAGER_LOGGER = logging.getLogger(f"{MODULE_NAME}.manager")
WORKER_LOGGER = logging.getLogger(f"{MODULE_NAME}.worker")
TASK_LOGGER = logging.getLogger(f"{MODULE_NAME}.task")


class WorkerState(Enum):
    BUSY = "busy"
    IDLE = "idle"
    TERMINATE = "terminate"
    QUIT = "quit"


class _WorkerDocument(Document):
    meta = {"collection": f"{MODULE_NAME}.worker"}

    name: str = StringField(required=True, unique=True)
    manager: str = StringField(required=True)
    state: WorkerState = EnumField(WorkerState, required=True)
    last_seen: datetime = DateTimeField(required=True)
    delay: float = FloatField(required=True)
    current_task: Optional["_TaskDocument"] = ReferenceField("Task")

class _WorkerLogDocument(MongoengineLogDocument):
    meta = {"collection": f"{MODULE_NAME}.worker.log",
            "indexes": ["manager"]}
    manager: _WorkerDocument = ReferenceField(_WorkerDocument, required=True)


class TaskState(Enum):
    NEW = "new"
    RUNNING = "running"  # running states
    CANCELING = "canceling"  # running states
    CANCELED = "canceled"  # final states
    FINISHED = "finished"  # final states
    FAILED = "failed"  # final states


class _TaskDocument(Document):
    meta = {"collection": f"{MODULE_NAME}.task"}

    name: str = StringField(required=True)
    manager: str = StringField(required=True)
    state: TaskState = EnumField(TaskState, required=True)
    worker: Optional[_WorkerDocument] = ReferenceField(_WorkerDocument)
    created_at: datetime = DateTimeField(required=True)
    due_at: datetime = DateTimeField(required=True)
    started_at: Optional[datetime] = DateTimeField()
    ended_at: Optional[datetime] = DateTimeField()
    params: dict[str, Any] = DictField(required=True)
    result: Optional[dict[str, Any]] = DictField()

class _TaskLogDocument(MongoengineLogDocument):
    meta = {"collection": f"{MODULE_NAME}.task.log",
            "indexes": ["task"]}
    task: _TaskDocument = ReferenceField(_TaskDocument, required=True)


class _BaseProxy:
    def __init__(self, proxy_document: Union[_WorkerDocument, _TaskDocument]):
        self._proxy_document = proxy_document

    def __str__(self):
        return f"{self.__class__.__name__}(name={self.name}, manager={self.manager}, state={self.state})"

    @property
    def id(self) -> ObjectId:
        return self._proxy_document.id

    @property
    def name(self) -> str:
        return self._proxy_document.name

    @property
    def manager(self) -> str:
        return self._proxy_document.manager

    @property
    def state(self) -> Union[WorkerState, TaskState]:
        self.reload()
        return self._proxy_document.state

    def reload(self) -> None:
        self._proxy_document.reload()

    def wait_for_state(self, *states: Union[WorkerState, TaskState], timeout: Optional[float] = None) -> None:
        start_time = time.perf_counter()
        while self.state not in states:
            if timeout is not None and time.perf_counter() - start_time > timeout:
                raise TimeoutError(f"Timeout while waiting for task '{self.name}' to reach state '{states}'")
            time.sleep(0.001)


class Worker(_BaseProxy):
    @property
    def state(self) -> WorkerState:
        return super().state

    @property
    def last_seen(self) -> datetime:
        self.reload()
        return self._proxy_document.last_seen

    @property
    def delay(self) -> float:
        self.reload()
        return self._proxy_document.delay

    @property
    def current_task(self) -> Optional["ScheduledTask"]:
        self.reload()
        if self._proxy_document.current_task is None:
            return None
        return ScheduledTask(proxy_document=self._proxy_document.current_task)

    def wait_for_state(self, *states: WorkerState, timeout: Optional[float] = None) -> None:
        super().wait_for_state(*states, timeout=timeout)

    def wait_for_task(self, timeout: Optional[float] = None) -> None:
        current_task = self.current_task
        if current_task is None:
            return
        current_task.wait_for_end(timeout=timeout)

    def terminate(self, wait: bool = False, timeout: Optional[float] = None) -> None:
        if self.state == WorkerState.TERMINATE:
            return
        elif self.state == WorkerState.QUIT:
            raise ValueError(f"Worker '{self.name}' is already quitting")
        self._proxy_document.state = WorkerState.TERMINATE
        self._proxy_document.save()
        if wait:
            self.wait_for_state(WorkerState.TERMINATE, timeout=timeout)


class ScheduledTask(_BaseProxy):
    @property
    def state(self) -> TaskState:
        return super().state

    @property
    def worker(self) -> Optional[Worker]:
        self.reload()
        if self._proxy_document.worker is None:
            return None
        return Worker(proxy_document=self._proxy_document.worker)

    @property
    def created_at(self) -> datetime:
        return self._proxy_document.created_at

    @property
    def due_at(self) -> datetime:
        return self._proxy_document.due_at

    @property
    def started_at(self) -> Optional[datetime]:
        self.reload()
        return self._proxy_document.started_at

    @property
    def ended_at(self) -> Optional[datetime]:
        self.reload()
        return self._proxy_document.ended_at

    @property
    def params(self) -> dict[str, Any]:
        return self._proxy_document.params.copy()

    @property
    def result(self) -> Optional[dict[str, Any]]:
        self.reload()
        if self._proxy_document.result is None:
            return None
        return self._proxy_document.result.copy()

    @property
    def duration(self) -> Optional[float]:
        self.reload()
        if self._proxy_document.started_at is None or self._proxy_document.ended_at is None:
            return None
        return (self._proxy_document.ended_at - self._proxy_document.started_at).total_seconds()

    @property
    def is_running(self) -> bool:
        return self.state in [TaskState.RUNNING, TaskState.CANCELING]

    def wait_for_state(self, *states: TaskState, timeout: Optional[float] = None) -> None:
        super().wait_for_state(*states, timeout=timeout)

    def wait_for_end(self, timeout: Optional[float] = None) -> None:
        self.wait_for_state(TaskState.FINISHED, TaskState.FAILED, TaskState.CANCELED, timeout=timeout)

    def cancel(self, wait: bool = False, timeout: Optional[float] = None) -> None:
        self.reload()
        if self._proxy_document.state == TaskState.CANCELING:
            return
        if self._proxy_document.state == TaskState.CANCELED:
            raise ValueError(f"Task '{self.name}' is already canceled")
        elif self._proxy_document.state == TaskState.FINISHED:
            raise ValueError(f"Task '{self.name}' is already finished")
        elif self._proxy_document.state == TaskState.FAILED:
            raise ValueError(f"Task '{self.name}' is already failed")

        self._proxy_document.state = TaskState.CANCELING
        self._proxy_document.save()

        if wait:
            self.wait_for_state(TaskState.CANCELED, timeout=timeout)


class _WorkerThread(threading.Thread):
    def __init__(self, manager: "Manager", worker_document: _WorkerDocument, loop_delay: float):
        super().__init__(name=worker_document.name, daemon=True)
        self.manager: Manager = manager
        self.worker_document: _WorkerDocument = worker_document
        self.loop_delay: float = loop_delay

        # creat worker logger
        self.logger = logging.getLogger(f"{LOGGER.name}.{WORKER_LOGGER.name}.{self.name}")
        worker_logger_handler = MongoengineLogHandler(document=_WorkerLogDocument,
                                                      document_kwargs={"manager": self.worker_document})
        if not isinstance(self.logger, SubLogger):
            self.logger.addHandler(worker_logger_handler)
        else:
            with self.logger.reconfigure():
                self.logger.addHandler(worker_logger_handler)

        self.logger.debug("Worker created")

        # set state to busy
        self.state = WorkerState.BUSY

        # get all running tasks for this worker and set them to failed
        for running_task in _TaskDocument.objects(worker=self.worker_document, state=TaskState.RUNNING).all():
            self.finish_task(task=running_task, success=False, result={"error": "Worker was restarted"})

    def update(self) -> None:
        self.worker_document.last_seen = local_now()
        self.worker_document.save()

    @property
    def state(self) -> WorkerState:
        self.worker_document.reload()
        return self.worker_document.state

    @state.setter
    def state(self, value: WorkerState) -> None:
        if value == self.worker_document.state:
            return
        self.worker_document.state = value
        self.update()
        self.logger.debug(f"Worker state set to {value}")

    def run(self) -> None:
        self.logger.debug("Worker started")

        delay = 0
        while self.state not in [WorkerState.TERMINATE, WorkerState.QUIT]:
            # get loop start time
            loop_start = time.perf_counter()

            # set delay
            self.worker_document.delay = delay

            # update document
            self.update()

            # set state to idle
            self.state = WorkerState.IDLE

            self.logger.debug("Worker running")

            # get next due task
            due_task: _TaskDocument = _TaskDocument.objects(manager=self.manager.name,
                                                            due_at__lte=local_now(),
                                                            state=TaskState.NEW,
                                                            worker=None).order_by("due_at").first()
            if due_task is not None:
                # start task
                due_task.state = TaskState.RUNNING
                due_task.worker = self.worker_document
                due_task.started_at = local_now()
                due_task.save()

                # set state to busy
                self.state = WorkerState.BUSY

                # run task
                self.task_runner(due_task)

            # get loop end time
            loop_end = time.perf_counter()

            # calculate delay
            delay = loop_end - loop_start

            # sleep for remaining time
            sleep_time = self.loop_delay - delay
            if sleep_time > 0:
                time.sleep(sleep_time)

        # set state to quit
        self.state = WorkerState.QUIT

        self.logger.debug("Worker stopped")

    def task_runner(self, task: _TaskDocument) -> None:
        self.logger.debug(f"Running task '{task.name}'")

        # create logger
        task_logger = logging.getLogger(f"{LOGGER.name}.{TASK_LOGGER.name}.{task.name}")

        # add logger handler
        task_logger_handler = MongoengineLogHandler(document=_TaskLogDocument,
                                                    document_kwargs={"task": task})
        if not isinstance(task_logger, SubLogger):
            task_logger.addHandler(task_logger_handler)
        else:
            with task_logger.reconfigure():
                task_logger.addHandler(task_logger_handler)

        # run task
        try:
            with LoggingContext(context_logger=task_logger) as logging_context:
                task_func = self.manager.get_task_func(task.name)
                task_result = task_func(**task.params)
                success = True
        except Exception as e:
            task_result = {"error": str(e)}
            success = False

        # remove logger handler and destroy it
        task_logger.removeHandler(task_logger_handler)
        task_logger_handler.destroy()

        # finish task
        self.finish_task(task, success, task_result)

    def finish_task(self, task: _TaskDocument, success: bool, result: dict[str, Any]) -> None:
        self.logger.debug(f"Finishing task '{task.name}'")

        # finish task
        task.reload()
        if task.state not in [TaskState.RUNNING, TaskState.CANCELING]:
            raise ValueError(f"Task '{self.name}' is not in state '{TaskState.RUNNING}' or '{TaskState.CANCELING}'")
        if task.state == TaskState.CANCELING:
            success = False
            result = {"error": "Task was canceled"}
        task.state = TaskState.FINISHED if success else TaskState.FAILED
        task.ended_at = local_now()
        task.result = result

        # save task
        try:
            task.save()
        except ValidationError as e:
            msg = f"Validation error while saving task '{task.name}': {e}"
            self.logger.error(msg)
            task.state = TaskState.FAILED
            task.result = {"error": msg}
            task.save()


class Manager:
    def __init__(self, name: Optional[str] = None, worker_loop_delay: Optional[float] = None):
        if name is None:
            name = "default"
        self._lock = threading.Lock()
        self._name: str = name
        self._logger = logging.getLogger(f"{LOGGER.name}.{MANAGER_LOGGER.name}.{self.name}")
        self._logger.debug("Manager created")
        self._workers: dict[str, ObjectId] = {}
        if worker_loop_delay is None:
            worker_loop_delay = 1.0
        self._worker_loop_delay: float = worker_loop_delay
        self._registered_tasks: dict[str, callable] = {}
        self._registered_tasks_param: dict[str, dict[str, type]] = {}
        self._registered_tasks_param_defaults: dict[str, dict[str, Any]] = {}

    @property
    def name(self) -> str:
        with self._lock:
            return self._name

    # --- worker management ---
    @property
    def worker_loop_delay(self) -> float:
        return self._worker_loop_delay

    @property
    def worker_count(self) -> int:
        return len(self._workers)

    @property
    def worker_names(self) -> list[str]:
        return list(self._workers.keys())

    @property
    def workers(self) -> list[Worker]:
        return [Worker(proxy_document=_WorkerDocument.objects.get(id=worker_id)) for worker_id in self._workers.values()]

    def create_worker(self, name: str) -> Worker:
        self._logger.debug(f"Creating worker '{name}'")

        if name in self.worker_names:
            raise ValueError(f"Worker with name '{name}' already exists")

        # get worker document
        try:
            worker_document = _WorkerDocument.objects.get(name=name)
        except DoesNotExist:
            worker_document = _WorkerDocument(name=name,
                                              manager=self.name,
                                              last_seen=local_now(),
                                              delay=0,
                                              state=WorkerState.BUSY)
            worker_document.save()

        # create worker
        worker = _WorkerThread(manager=self, worker_document=worker_document, loop_delay=self._worker_loop_delay)

        # add worker name and id to workers
        with self._lock:
            self._workers[name] = worker_document.id

        # start worker
        worker.start()

        return Worker(proxy_document=worker_document)

    # --- task management ---

    @property
    def registered_tasks(self) -> list[str]:
        with self._lock:
            return list(self._registered_tasks.keys())

    def get_task_func(self, name: str) -> callable:
        with self._lock:
            if name not in self._registered_tasks:
                raise ValueError(f"No task function with name '{name}' found")
            return self._registered_tasks[name]

    def registering_task(self, name: Optional[str] = None, func: callable = None) -> callable:
        if self.worker_count > 0:
            raise RuntimeError("Cannot register tasks after workers are created")
        if not callable(func):
            raise ValueError(f"Argument 'func' must be a callable not '{type(func)}'")
        with self._lock:
            # get name from function if not provided
            if name is None:
                name = func.__name__

            self._logger.debug(f"Registering task '{name}'")

            # check if task with name already registered
            if name in self._registered_tasks:
                raise ValueError(f"Task with name '{name}' already registered")

            # register task
            self._registered_tasks[name] = func
            self._registered_tasks_param[name] = {}
            self._registered_tasks_param_defaults[name] = {}

            # get signature from function
            func_params = dict(inspect.signature(func).parameters)
            for param_name, param in func_params.items():
                self._registered_tasks_param[name][param_name] = param.annotation
                if param.default != inspect.Parameter.empty:
                    self._registered_tasks_param_defaults[name][param_name] = param.default

            return func

    def register_task(self, name: Optional[str] = None):
        def decorator(func: callable = None):
            return self.registering_task(name=name, func=func)

        return decorator

    def schedule_task(self, name: str, due: Optional[datetime] = None, **given_task_params) -> ScheduledTask:
        self._logger.debug(f"Scheduling task '{name}'")

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
            created_at=local_now(),
            due_at=due or local_now(),
            params=given_task_params
        )
        task.save()

        return ScheduledTask(proxy_document=task)
