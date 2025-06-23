import logging
import multiprocessing
import threading
from datetime import datetime as _datetime
from enum import Enum
from typing import Optional, Union, TYPE_CHECKING

from wiederverwendbar.task_manger.task import Task
from wiederverwendbar.timer import timer_loop

if TYPE_CHECKING:
    from wiederverwendbar.task_manger.trigger import Trigger


class TaskManagerStates(str, Enum):
    INITIAL = "INITIAL"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"


class TaskManager:
    class States(str, Enum):
        INITIAL = "INITIAL"
        RUNNING = "RUNNING"
        STOPPED = "STOPPED"

    lock = threading.Lock()

    def __init__(self,
                 name: Optional[str] = None,
                 worker_count: Optional[int] = None,
                 daemon: bool = False,
                 loop_delay: Optional[float] = None,
                 logger: Optional[logging.Logger] = None):
        self._id = id(self)
        if name is None:
            name = self.__class__.__name__
        self._name = name
        self._workers: list[threading.Thread] = []
        self._tasks: list[Task] = []
        self._state: TaskManagerStates = TaskManagerStates.INITIAL
        self._creation_time: _datetime = _datetime.now()
        self._start_time: Optional[_datetime] = None
        self.logger = logger or logging.getLogger(self._name)

        # create workers
        if worker_count is None:
            worker_count = multiprocessing.cpu_count()
            worker_count = round(worker_count / 2)
            if worker_count < 1:
                worker_count = 1
        for i in range(worker_count):
            worker = threading.Thread(name=f"{self._name}.Worker{i}", target=self.loop, daemon=daemon)
            self._workers.append(worker)

        # set loop delay
        if loop_delay is None:
            if self.worker_count >= 1:
                loop_delay = 0.001
        self._loop_delay = loop_delay

    def __str__(self):
        return f"{self.__class__.__name__}(name={self._name}, id={self._id}, state={self._state.value})"

    def __del__(self):
        if self.state == TaskManagerStates.RUNNING:
            self.stop()

    @property
    def worker_count(self) -> int:
        """
        Number of workers.

        :return: int
        """

        return len(self._workers)

    @property
    def state(self) -> TaskManagerStates:
        """
        Manager state

        :return: TaskManagerStates
        """

        with self.lock:
            return self._state

    @property
    def creation_time(self) -> _datetime:
        """
        Manager creation time.

        :return: datetime
        """

        with self.lock:
            return self._creation_time

    @property
    def start_time(self) -> Optional[_datetime]:
        """
        Manager start time.

        :return: datetime or None
        """

        with self.lock:
            return self._start_time

    def start(self) -> None:
        """
        Start manager.

        :return: None
        """

        if self.state != TaskManagerStates.INITIAL:
            raise ValueError(f"Manager '{self._name}' is not in state '{TaskManagerStates.INITIAL.value}'.")

        self.logger.debug(f"Starting manager {self} ...")

        with self.lock:
            self._state = TaskManagerStates.RUNNING

        # start workers
        for worker in self._workers:
            self.logger.debug(f"{self} -> Starting worker '{worker.name}' ...")
            worker.start()

        # set the start time
        with self.lock:
            self._start_time = _datetime.now()

        self.logger.debug(f"Manager {self} started.")

    def stop(self) -> None:
        """
        Stop manager.

        :return: None
        """

        if self.state != TaskManagerStates.RUNNING:
            raise ValueError(f"Manager {self} is not in state '{TaskManagerStates.RUNNING.value}'.")

        self.logger.debug(f"Stopping manager {self} ...")

        # set stopped flag
        with self.lock:
            self._state = TaskManagerStates.STOPPED

        # wait for workers to finish
        for worker in self._workers:
            if worker.is_alive():
                self.logger.debug(f"{self} -> Waiting for worker '{worker.name}' to finish ...")
                worker.join()

        self.logger.debug(f"Manager {self} stopped.")

    def loop(self, stay_in_loop: bool = True) -> None:
        """
        Manager loop. All workers run this loop. If worker_count is 0, you can run this loop manually.

        :param stay_in_loop: Stay in loop flag. If False, loop will break after the first task is run.
        :return: None
        """

        if self.state != TaskManagerStates.RUNNING:
            raise ValueError(f"Manager {self} is not in state '{TaskManagerStates.RUNNING.value}'.")

        # check if running in a worker thread
        with self.lock:
            if threading.current_thread() not in self._workers:
                if len(self._workers) > 0:
                    raise ValueError(f"{self} -> Running manager loop outside of worker thread is not allowed, if worker_count > 0.")

        while self.state == TaskManagerStates.RUNNING:
            # get the next task from the list
            task = None
            with self.lock:
                for i, _task in enumerate(self._tasks):
                    if not _task():
                        continue
                    task = self._tasks.pop(i)
                    break

            # if a task to run available, run the task
            if task is not None:
                self.logger.debug(f"{self} -> Running task {task} ...")
                if task.time_measurement == Task.TimeMeasurement.START:
                    task._last_run = _datetime.now()
                try:
                    task.payload()
                    self.logger.debug(f"{self} -> Task {task} successfully run.")
                except Exception as e:
                    self.logger.error(f"{self} -> Task {task} failed: {e}")
                if task.time_measurement == Task.TimeMeasurement.END:
                    task._last_run = _datetime.now()

                # put the task back to list
                with self.lock:
                    self._tasks.append(task)

            if not stay_in_loop:
                break
            if self._loop_delay:
                timer_loop(name=f"{self._name}_{self._id}_LOOP", seconds=self._loop_delay, loop_delay=self._loop_delay)

    def add_task(self, task: Task) -> None:
        """
        Add task to manager.

        :param task:
        :return:
        """

        task.manager = self

    def remove_task(self, task: Task) -> None:
        """
        Remove task from manager.

        :param task:
        :return:
        """

        if task.manager is not self:
            raise ValueError(f"Task {task} is not assigned to manager {self}.")
        task.manager = None

    def task(self,
             *triggers: "Trigger",
             name: Optional[str] = None,
             time_measurement: Optional[Task.TimeMeasurement] = None,
             task_args: Optional[Union[list, tuple]] = None,
             task_kwargs: Optional[dict] = None):
        """
        Task decorator.

        :param triggers: The trigger of the task.
        :param name: The name of the task.
        :param time_measurement: Time measurement for the task.
        :param task_args: Args for the task payload.
        :param task_kwargs: Kwargs for the task payload.
        :return: Task or function
        """

        def decorator(func):
            self.add_task(task=Task(func,
                                    *triggers,
                                    name=name,
                                    time_measurement=time_measurement,
                                    task_args=task_args,
                                    task_kwargs=task_kwargs))
            return func

        return decorator
