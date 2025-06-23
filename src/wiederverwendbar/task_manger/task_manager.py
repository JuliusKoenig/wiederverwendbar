import logging
import multiprocessing
import threading
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from wiederverwendbar.task_manger.task import Task
from wiederverwendbar.task_manger.trigger import Trigger
from wiederverwendbar.timer import timer_loop


class TaskManagerStates(str, Enum):
    INITIAL = "INITIAL"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"


class TaskManager:
    lock = threading.Lock()

    def __init__(self,
                 name: Optional[str] = None,
                 worker_count: Optional[int] = None,
                 daemon: bool = False,
                 keep_done_tasks: bool = False,
                 loop_delay: Optional[float] = None,
                 logger: Optional[logging.Logger] = None,
                 log_self: bool = True):
        self._id = id(self)
        if name is None:
            name = self.__class__.__name__
        self._name = name
        self._workers: list[threading.Thread] = []
        self._tasks: list[Task] = []
        self._state: TaskManagerStates = TaskManagerStates.INITIAL
        self._creation_time: datetime = datetime.now()
        self._keep_done_tasks = keep_done_tasks
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
    def creation_time(self) -> datetime:
        """
        Manager creation time.

        :return: datetime
        """

        with self.lock:
            creation_time = self._creation_time
        return creation_time

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

    def _pop_task(self) -> Optional[Task]:
        next_task = None
        with self.lock:
            for i, task in enumerate(self._tasks):
                if task.next_run is None:
                    continue
                if task.next_run > datetime.now():
                    continue
                next_task = self._tasks.pop(i)
                break
        return next_task

    def _run_task(self, task: Task) -> None:
        self.logger.debug(f"{self} -> Running task {task} ...")

        with self.lock:
            if task.time_measurement_before_run:
                task.set_last_run()
                task.set_next_run()

        # run task
        task.payload()

        self.logger.debug(f"{self} -> Task {task} successfully run.")

        with self.lock:
            if not task.time_measurement_before_run:
                task.set_last_run()
                task.set_next_run()

    def _append_task(self, task: Task) -> None:
        with self.lock:
            if not task.is_done:
                self._tasks.append(task)
            else:
                self.logger.debug(f"{self} -> Task {task} is done.")
                if self._keep_done_tasks:
                    self._tasks.append(task)

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
            task = self._pop_task()
            if task is not None:
                self._run_task(task)
                self._append_task(task)

            if not stay_in_loop:
                break
            if self._loop_delay:
                timer_loop(name=f"{self._name}_{self._id}_LOOP", seconds=self._loop_delay, loop_delay=self._loop_delay)

    def add_task(self, task: Task):
        """
        Add task to manager.

        :param task:
        :return:
        """

        task.init(self)
        with self.lock:
            self._tasks.append(task)
        self.logger.debug(f"{self} -> Task {task} added.")

    def remove_task(self, task: Task):
        """
        Remove task from manager.

        :param task:
        :return:
        """

        with self.lock:
            self._tasks.remove(task)
        self.logger.debug(f"{self} -> Task {task.name} removed.")

    def task(self,
             name: Optional[str] = None,
             trigger: Optional[Trigger] = None,
             time_measurement_before_run: bool = True,
             return_func: bool = True,
             *args,
             **kwargs) -> Any:
        """
        Task decorator.

        :param name: The name of the task.
        :param trigger: The trigger of the task.
        :param time_measurement_before_run: Time measurement before run flag.
        :param return_func: Return function flag. If True, the function will be returned instead of the task.
        :param args: Args for the task payload.
        :param kwargs: Kwargs for the task payload.
        :return: Task or function
        """

        def decorator(func):
            task = Task(name=name,
                        manager=self,
                        trigger=trigger,
                        time_measurement_before_run=time_measurement_before_run,
                        payload=func,
                        auto_add=True,
                        *args,
                        **kwargs)
            return task if not return_func else func

        return decorator
