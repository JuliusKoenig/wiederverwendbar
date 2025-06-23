from datetime import datetime as _datetime
from enum import Enum
from typing import Any, Optional, Callable, Union, TYPE_CHECKING

from wiederverwendbar.functions.is_coroutine_function import is_coroutine_function
from wiederverwendbar.task_manger.trigger import Trigger

if TYPE_CHECKING:
    from wiederverwendbar.task_manger.task_manager import TaskManager


class Task:
    class TimeMeasurement(str, Enum):
        START = "START"
        END = "END"

    def __init__(self,
                 payload: Callable[..., None],
                 *triggers: Trigger,
                 name: Optional[str] = None,
                 time_measurement: Optional[TimeMeasurement] = None,
                 task_args: Optional[Union[list, tuple]] = None,
                 task_kwargs: Optional[dict] = None):
        self._manager = None

        # set the task name
        if name is None:
            name = payload.__name__
        self._name = name

        # set task triggers
        self._triggers = []
        for trigger in triggers:
            if not isinstance(trigger, Trigger):
                raise ValueError("Trigger must be an instance of Trigger.")
            if trigger.task is not None:
                raise ValueError("Trigger already assigned to a task.")
            trigger._task = self
            self._triggers.append(trigger)
        self._triggers = tuple(self._triggers)

        # set task payload
        if not callable(payload):
            raise ValueError("Payload must be callable.")
        if is_coroutine_function(payload):
            raise ValueError("Coroutine functions are not supported.")
        self._payload = payload

        # indicates when the last run time should be measured
        if time_measurement is None:
            time_measurement = self.TimeMeasurement.START
        if not isinstance(time_measurement, self.TimeMeasurement):
            raise ValueError("Time measurement must be an instance of TaskTimeMeasurement.")
        self._time_measurement = time_measurement

        # set payload args and kwargs
        if task_args is None:
            task_args = []
        if not iter(task_args):
            raise ValueError("Task args must be iterable.")
        self._task_args = tuple(task_args)
        if task_kwargs is None:
            task_kwargs = {}
        if not isinstance(task_kwargs, dict):
            raise ValueError("Task kwargs must be dict.")
        self._task_kwargs = task_kwargs

        # indicate last run
        self._last_run = None

        # indicate if the task is done
        self._done = False

    def __str__(self):
        return (f"{self.__class__.__name__}("
                f"name={self.name}, "
                f"trigger=[{', '.join([str(trigger) for trigger in self._triggers])}], "
                f"last_run={self.last_run})")

    def __call__(self, *args, **kwargs) -> bool:
        if self.manager is None:
            raise ValueError(f"Task {self} is not assigned to a manager.")
        for trigger in self.triggers:
            if trigger():
                return True
        return False

    @property
    def manager(self) -> Optional["TaskManager"]:
        return self._manager

    @manager.setter
    def manager(self, manager: "TaskManager") -> None:
        if manager is None:
            if self._manager is None:
                return
            manager = self._manager
            with manager.lock:
                # noinspection PyProtectedMember
                manager._tasks.remove(self)
            self.manager_removed()
        else:
            if self._manager is not None:
                raise ValueError(f"Task {self} is already assigned to manager {self._manager}.")
            self._manager = manager

            with manager.lock:
                # noinspection PyProtectedMember
                manager._tasks.append(self)
            self.manager_added()

    @property
    def name(self) -> str:
        return self._name

    @property
    def triggers(self) -> tuple[Trigger, ...]:
        return self._triggers

    @property
    def time_measurement(self) -> TimeMeasurement:
        return self._time_measurement

    @property
    def task_args(self) -> tuple[Any]:
        return self._task_args

    @property
    def task_kwargs(self) -> dict[str, Any]:
        return self._task_kwargs

    @property
    def last_run(self) -> Optional[_datetime]:
        return self._last_run

    def manager_added(self) -> None:
        for trigger in self.triggers:
            trigger.manager_added()
        self.manager.logger.debug(f"{self.manager} -> Task {self} added.")

    def manager_removed(self) -> None:
        for trigger in self.triggers:
            trigger.manager_removed()
        self.manager.logger.debug(f"{self.manager} -> Task {self} removed.")

    def payload(self) -> None:
        self._payload(*self.task_args, **self.task_kwargs)
