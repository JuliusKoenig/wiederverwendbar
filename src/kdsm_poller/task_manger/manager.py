import logging
import multiprocessing
import threading
import time
from datetime import datetime

from kdsm_poller.task_manger.task import Task
from wiederverwendbar.singleton import Singleton

LOGGER = logging.getLogger(__name__)


class Manager:
    lock = threading.Lock()

    def __init__(self,
                 name: str | None = None,
                 worker_count: int | None = None,
                 daemon: bool = False,
                 keep_done_tasks: bool = True,
                 loop_delay: float | None = None,
                 logger: logging.Logger | None = None):
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
        return len(self._workers)

    @property
    def stopped(self):
        with self.lock:
            stopped = self._stopped
        return stopped

    @property
    def creation_time(self):
        with self.lock:
            creation_time = self._creation_time
        return creation_time

    def start(self):
        self.logger.debug(f"{self}: Starting manager ...")

        # start workers
        for worker in self._workers:
            self.logger.debug(f"{self}: Starting worker '{worker.name}' ...")
            worker.start()

        self.logger.debug(f"{self}: Manager started.")

    def stop(self):
        self.logger.debug(f"{self}: Stopping manager ...")

        # set stopped flag
        with self.lock:
            self._stopped = True

        # wait for workers to finish
        for worker in self._workers:
            self.logger.debug(f"{self}: Waiting for worker '{worker.name}' to finish ...")
            worker.join()

        self.logger.debug(f"{self}: Manager stopped.")

    def loop(self, stay_in_loop: bool | None = None):
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
        task.init(self)
        with self.lock:
            self._tasks.append(task)
        self.logger.debug(f"{self}: Task '{task}' added.")

    def remove_task(self, task: Task):
        with self.lock:
            self._tasks.remove(task)
        self.logger.debug(f"{self}: Task '{task}' removed.")


class ManagerSingleton(Manager, metaclass=Singleton):
    ...
