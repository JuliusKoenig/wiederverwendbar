from datetime import datetime
from typing import Optional

from wiederverwendbar.task_manger.trigger import Trigger, Interval, At


class Task:
    def __init__(self,
                 payload,
                 manager=None,
                 name: Optional[str] = None,
                 trigger: Optional[Trigger] = None,
                 time_measurement_before_run: bool = True,
                 auto_add: Optional[bool] = None,
                 *args,
                 **kwargs):
        # set task name
        if name is None:
            name = payload.__name__
        self.name = name

        self.manager = None

        # set task trigger
        if not isinstance(trigger, (Interval, At)):
            raise ValueError("Invalid trigger object.")
        self.trigger = trigger

        # set task payload
        if not callable(payload):
            raise ValueError("Payload must be callable.")
        self._payload = payload

        # set payload args and kwargs
        self.args = []
        self.kwargs = {}
        if not iter(args):
            raise ValueError("Args must be iterable.")
        for arg in args:
            self.args.append(arg)
        if not isinstance(kwargs, dict):
            raise ValueError("Kwargs must be dict.")
        self.kwargs = kwargs

        self.time_measurement_before_run = time_measurement_before_run

        self._last_run: Optional[datetime] = None
        self._next_run: Optional[datetime] = None

        # indicate if task is done
        self._done = False

        # auto add task to manager
        if auto_add is None:
            auto_add = True if manager else False

        if auto_add:
            if not manager:
                raise ValueError("Manager object is required.")
            manager.add_task(self)

    def __str__(self):
        return f"{self.manager.name}.{self.name}"

    def init(self, manager):
        self.manager = manager
        self.trigger.init(manager)
        self.set_next_run()

        # log task creation
        self.manager.logger.debug(f"{self}: Task created.")

    @property
    def last_run(self) -> Optional[datetime]:
        if self._last_run is None:
            return datetime.fromtimestamp(0)
        return self._last_run

    @property
    def next_run(self) -> Optional[datetime]:
        if self.is_done:
            return None
        return self._next_run

    @property
    def is_done(self) -> bool:
        return self._done

    def set_next_run(self):
        if isinstance(self.trigger, Interval):
            next_run = self.trigger.next(self.last_run)
        elif isinstance(self.trigger, At):
            next_run = self.trigger.next()
            if next_run == self._next_run:
                self.done()
        else:
            raise ValueError("Invalid trigger object.")
        self._next_run = next_run

    def set_last_run(self):
        self._last_run = datetime.now()

    def done(self):
        self._done = True

    def payload(self):
        self._payload(*self.args, **self.kwargs)
