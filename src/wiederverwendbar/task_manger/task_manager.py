import logging
import multiprocessing
import threading
import time
from datetime import datetime
from typing import Any, Optional

from wiederverwendbar.task_manger.task import Task
from wiederverwendbar.task_manger.trigger import Trigger

LOGGER = logging.getLogger(__name__)


class TaskManager:
    lock = threading.Lock()

    def __init__(self,
                 name: Optional[str] = None,
                 worker_count: Optional[int] = None,
                 daemon: bool = False,
                 keep_done_tasks: bool = False,
                 loop_delay: Optional[float] = None,
                 logger: Optional[logging.Logger] = None):
        if name is None:
            name = self.__class__.__name__
        self.name = name
        self._workers: list[threading.Thread] = []
        self._tasks: list[Task] = []
        self._stopped: bool = False
        self._creation_time: datetime = datetime.now()
        self._keep_done_tasks = keep_done_tasks
        self.logger = logger or LOGGER

        # create workers
        if worker_count is None:
            worker_count = multiprocessing.cpu_count()
            if worker_count - 2 < 1:
                worker_count = 1
            if worker_count > 4:
                worker_count = 4
        for i in range(worker_count):
            worker = threading.Thread(name=f"{self.name}.Worker{i}", target=self.loop, daemon=daemon)
            self._workers.append(worker)

        # set loop delay
        if loop_delay is None:
            if self.worker_count > 1:
                loop_delay = 0.001
        self._loop_delay = loop_delay

    def __str__(self):
        return f"{self.__class__.__name__}({self.name})"

    def __del__(self):
        if not self.stopped:
            self.stop()

    @property
    def worker_count(self):
        """
        Number of workers.

        :return: int
        """

        return len(self._workers)

    @property
    def stopped(self):
        """
        Manager stopped flag.

        :return: bool
        """

        with self.lock:
            stopped = self._stopped
        return stopped

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

        self.logger.debug(f"{self}: Starting manager ...")

        # start workers
        for worker in self._workers:
            self.logger.debug(f"{self}: Starting worker '{worker.name}' ...")
            worker.start()

        self.logger.debug(f"{self}: Manager started.")

    def stop(self) -> None:
        """
        Stop manager.

        :return: None
        """

        self.logger.debug(f"{self}: Stopping manager ...")

        # set stopped flag
        with self.lock:
            self._stopped = True

        # wait for workers to finish
        for worker in self._workers:
            if worker.is_alive():
                self.logger.debug(f"{self}: Waiting for worker '{worker.name}' to finish ...")
                worker.join()

        self.logger.debug(f"{self}: Manager stopped.")

    def loop(self, stay_in_loop: Optional[bool] = None) -> None:
        """
        Manager loop. All workers run this loop. If worker_count is 0, you can run this loop manually.

        :param stay_in_loop: Stay in loop flag. If False, loop will break after the first task is run.
        :return: None
        """

        if stay_in_loop is None:
            with self.lock:
                stay_in_loop = bool(self._loop_delay)
        while not self.stopped:
            now = datetime.now()
            current_task = None
            with self.lock:
                for i, task in enumerate(self._tasks):
                    if task.next_run is None:
                        continue
                    if task.next_run > now:
                        continue
                    current_task = self._tasks.pop(i)
                    break
            if current_task is None:
                with self.lock:
                    loop_delay = self._loop_delay
                if loop_delay:
                    time.sleep(loop_delay)
                continue

            self.logger.debug(f"{self}: Running task '{current_task}' ...")

            with self.lock:
                if current_task.time_measurement_before_run:
                    current_task.set_last_run()
                    current_task.set_next_run()

            # run task
            current_task.payload()

            self.logger.debug(f"{self}: Task '{current_task}' successfully run.")

            with self.lock:
                if not current_task.time_measurement_before_run:
                    current_task.set_last_run()
                    current_task.set_next_run()
                if not current_task.is_done:
                    self._tasks.append(current_task)
                else:
                    self.logger.debug(f"{self}: Task '{current_task}' is done.")
                    if self._keep_done_tasks:
                        self._tasks.append(current_task)

            if not stay_in_loop:
                break

    def add_task(self, task: Task):
        """
        Add task to manager.

        :param task:
        :return:
        """

        task.init(self)
        with self.lock:
            self._tasks.append(task)
        self.logger.debug(f"{self}: Task '{task}' added.")

    def remove_task(self, task: Task):
        """
        Remove task from manager.

        :param task:
        :return:
        """

        with self.lock:
            self._tasks.remove(task)
        self.logger.debug(f"{self}: Task '{task}' removed.")

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


