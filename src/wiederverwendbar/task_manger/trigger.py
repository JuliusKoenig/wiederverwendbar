import threading
from abc import ABC, abstractmethod
from datetime import datetime as _datetime, timedelta
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from wiederverwendbar.task_manger.task import Task


class Trigger(ABC):
    def __init__(self):
        self.lock = threading.Lock()
        self._task = None

    def __str__(self):
        return f"{self.__class__.__name__}()"

    def __call__(self):
        if self.task is None:
            raise ValueError(f"Trigger {self} is not assigned to a task.")
        return self.check()

    def manager_added(self) -> None:
        ...

    def manager_removed(self) -> None:
        ...

    @property
    def task(self) -> Optional["Task"]:
        return self._task

    @abstractmethod
    def check(self) -> bool:
        ...


class Interval(Trigger):
    def __init__(self,
                 seconds: float = 0,
                 minutes: int = 0,
                 hours: int = 0,
                 days: int = 0,
                 weeks: int = 0,
                 months: int = 0,
                 years: int = 0):
        super().__init__()

        # calculate the interval in seconds
        self._interval = float(seconds)
        self._interval += minutes * 60
        self._interval += hours * 60 * 60
        self._interval += days * 60 * 60 * 24
        self._interval += weeks * 60 * 60 * 24 * 7
        self._interval += months * 60 * 60 * 24 * 30
        self._interval += years * 60 * 60 * 24 * 365

    def __str__(self):
        interval = self.interval
        interval_str = f"{self.__class__.__name__}(Every "
        if interval >= 60 * 60 * 24 * 365:
            years = interval // (60 * 60 * 24 * 365)
            interval_str += f"{years}y "
            interval -= years * 60 * 60 * 24 * 365
        if interval >= 60 * 60 * 24 * 30:
            months = interval // (60 * 60 * 24 * 30)
            interval_str += f"{months}M "
            interval -= months * 60 * 60 * 24 * 30
        if interval >= 60 * 60 * 24 * 7:
            weeks = interval // (60 * 60 * 24 * 7)
            interval_str += f"{weeks}w "
            interval -= weeks * 60 * 60 * 24 * 7
        if interval >= 60 * 60 * 24:
            days = interval // (60 * 60 * 24)
            interval_str += f"{days}d "
            interval -= days * 60 * 60 * 24
        if interval >= 60 * 60:
            hours = interval // (60 * 60)
            interval_str += f"{hours}h "
            interval -= hours * 60 * 60
        if interval >= 60:
            minutes = interval // 60
            interval_str += f"{minutes}m "
            interval -= minutes * 60
        if interval > 0:
            interval_str += f"{interval}s "
        interval_str = interval_str.strip() + ")"
        return interval_str

    def __int__(self):
        return round(self.interval)

    def __float__(self):
        return self.interval

    def __add__(self, other):
        if isinstance(other, (Interval, int, float)):
            return Interval(seconds=float(self) + float(other))
        raise ValueError("Only Interval, int and float are supported.")

    @property
    def interval(self) -> float:
        with self.lock:
            return self._interval

    @interval.setter
    def interval(self, value: float):
        with self.lock:
            self._interval = value

    def check(self) -> bool:
        if self.task.last_run is None:
            return True
        if _datetime.now() - self.task.last_run > timedelta(seconds=self.interval):
            return True
        return False


class EverySeconds(Interval):
    def __init__(self, seconds: float):
        super().__init__(seconds=seconds)


class EveryMinutes(Interval):
    def __init__(self, minutes: int):
        super().__init__(minutes=minutes)


class EveryHours(Interval):
    def __init__(self, hours: int):
        super().__init__(hours=hours)


class EveryDays(Interval):
    def __init__(self, days: int):
        super().__init__(days=days)


class EveryWeeks(Interval):
    def __init__(self, weeks: int):
        super().__init__(weeks=weeks)


class EveryMonths(Interval):
    def __init__(self, months: int):
        super().__init__(minutes=months)


class EveryYears(Interval):
    def __init__(self, years: int):
        super().__init__(years=years)


class At(Trigger):
    def __init__(self,
                 second: Optional[int] = None,
                 minute: Optional[int] = None,
                 hour: Optional[int] = None,
                 day: Optional[int] = None,
                 month: Optional[int] = None,
                 year: Optional[int] = None):
        super().__init__()

        self._second: Optional[int] = second
        self._minute: Optional[int] = minute
        self._hour: Optional[int] = hour
        self._day: Optional[int] = day
        self._month: Optional[int] = month
        self._year: Optional[int] = year

    @property
    def second(self) -> Optional[int]:
        with self.lock:
            return self._second

    @second.setter
    def second(self, value: Optional[int]):
        with self.lock:
            self._second = value

    @property
    def minute(self) -> Optional[int]:
        with self.lock:
            return self._minute

    @minute.setter
    def minute(self, value: Optional[int]):
        with self.lock:
            self._minute = value

    @property
    def hour(self) -> Optional[int]:
        with self.lock:
            return self._hour

    @hour.setter
    def hour(self, value: Optional[int]):
        with self.lock:
            self._hour = value

    @property
    def day(self) -> Optional[int]:
        with self.lock:
            return self._day

    @day.setter
    def day(self, value: Optional[int]):
        with self.lock:
            self._day = value

    @property
    def month(self) -> Optional[int]:
        with self.lock:
            return self._month

    @month.setter
    def month(self, value: Optional[int]):
        with self.lock:
            self._month = value

    @property
    def year(self) -> Optional[int]:
        with self.lock:
            return self._year

    @year.setter
    def year(self, value: Optional[int]):
        with self.lock:
            self._year = value

    def manager_added(self) -> None:
        super().manager_added()

        # check if some values are set
        if not any([self.second is not None, self.minute is not None, self.hour is not None, self.day is not None, self.month is not None, self.year is not None]):
            raise ValueError("At least one of the values must be set.")

        # validate values
        if self.second is not None and not 0 <= self.second <= 59:
            raise ValueError(f"Second must be in range 0-59. Got '{self.second}'.")
        if self.minute is not None and not 0 <= self.minute <= 59:
            raise ValueError(f"Minute must be in range 0-59. Got '{self.minute}'.")
        if self.hour is not None and not 0 <= self.hour <= 23:
            raise ValueError(f"Hour must be in range 0-23. Got '{self.hour}'.")
        if self.day is not None and not 1 <= self.day <= 31:
            raise ValueError(f"Day must be in range 1-31. Got '{self.day}'.")
        if self.month is not None and not 1 <= self.month <= 12:
            raise ValueError(f"Month must be in range 1-12. Got '{self.month}'.")
        if self.year is not None and not 1970 <= self.year <= 9999:
            raise ValueError(f"Year must be in range 1970-9999. Got '{self.year}'.")

    def __str__(self):
        at_str = "At "
        if self.year is not None:
            at_str += f"year {self.year:04} "
        if self.month is not None:
            if at_str != "At ":
                at_str += "and "
            at_str += f"month {self.month:02} "
        if self.day is not None:
            if at_str != "At ":
                at_str += "and "
            at_str += f"day {self.day:02} "
        if self.hour is not None:
            if at_str != "At ":
                at_str += "and "
            at_str += f"hour {self.hour:02} "
        if self.minute is not None:
            if at_str != "At ":
                at_str += "and "
            at_str += f"minute {self.minute:02} "
        if self.second is not None:
            if at_str != "At ":
                at_str += "and "
            at_str += f"second {self.second:02} "
        at_str = at_str.strip()
        return f"{self.__class__.__name__}({at_str})"

    def check(self) -> bool:
        next_run = _datetime.now().replace(microsecond=0)

        second = 0
        if self.second is not None:
            second = self.second
            second_n = next_run.replace(second=second)
            if second_n < next_run:
                next_run += timedelta(minutes=1)
            if self.task.last_run is not None:
                if second_n < self.task.last_run:
                    next_run += timedelta(minutes=1)
            next_run = next_run.replace(second=second)

        minute = 0
        if self.minute is not None:
            minute = self.minute
            minute_n = next_run.replace(minute=minute)
            if minute_n < next_run:
                next_run += timedelta(hours=1)
            if self.task.last_run is not None:
                if minute_n < self.task.last_run:
                    next_run += timedelta(hours=1)
            next_run = next_run.replace(minute=minute, second=second)

        hour = 0
        if self.hour is not None:
            hour = self.hour
            hour_n = next_run.replace(hour=hour)
            if hour_n < next_run:
                next_run += timedelta(days=1)
            if self.task.last_run is not None:
                if hour_n < self.task.last_run:
                    next_run += timedelta(days=1)
            next_run = next_run.replace(hour=hour, minute=minute, second=second)

        day = 1
        if self.day is not None:
            day = self.day
            day_n = next_run.replace(day=day)
            if day_n < next_run:
                while True:
                    next_run += timedelta(days=1)
                    if next_run.day == day:
                        break
            if self.task.last_run is not None:
                if day_n < self.task.last_run:
                    while True:
                        next_run += timedelta(days=1)
                        if next_run.day == day:
                            break
            next_run = next_run.replace(day=day, hour=hour, minute=minute, second=second)

        month = 1
        if self.month is not None:
            month = self.month
            month_n = next_run.replace(month=month)
            if month_n < next_run:
                while True:
                    next_run += timedelta(days=1)
                    if next_run.month == month:
                        break
            if self.task.last_run is not None:
                if month_n < self.task.last_run:
                    while True:
                        next_run += timedelta(days=1)
                        if next_run.month == month:
                            break
            next_run = next_run.replace(month=month, day=day, hour=hour, minute=minute, second=second)

        if self.year is not None:
            next_run = next_run.replace(year=self.year, month=month, day=day, hour=hour, minute=minute, second=second)

        if next_run <= _datetime.now():
            return True
        return False


class AtDatetime(Trigger):
    def __init__(self,
                 datetime: Optional[_datetime] = None,
                 delay_for_seconds: int = 0,
                 delay_for_minutes: int = 0,
                 delay_for_hours: int = 0,
                 delay_for_days: int = 0):
        super().__init__()

        self._datetime = datetime
        self._delay_for_seconds = delay_for_seconds
        self._delay_for_minutes = delay_for_minutes
        self._delay_for_hours = delay_for_hours
        self._delay_for_days = delay_for_days

    @property
    def datetime(self) -> Optional[_datetime]:
        with self.lock:
            return self._datetime

    @datetime.setter
    def datetime(self, value: Optional[_datetime]):
        with self.lock:
            self._datetime = value

    @property
    def delay_for_seconds(self) -> int:
        with self.lock:
            return self._delay_for_seconds

    @delay_for_seconds.setter
    def delay_for_seconds(self, value: int):
        with self.lock:
            self._delay_for_seconds = value

    @property
    def delay_for_minutes(self) -> int:
        with self.lock:
            return self._delay_for_minutes

    @delay_for_minutes.setter
    def delay_for_minutes(self, value: int):
        with self.lock:
            self._delay_for_minutes = value

    @property
    def delay_for_hours(self) -> int:
        with self.lock:
            return self._delay_for_hours

    @delay_for_hours.setter
    def delay_for_hours(self, value: int):
        with self.lock:
            self._delay_for_hours = value

    @property
    def delay_for_days(self) -> int:
        with self.lock:
            return self._delay_for_days

    @delay_for_days.setter
    def delay_for_days(self, value: int):
        with self.lock:
            self._delay_for_days = value

    def manager_added(self) -> None:
        super().manager_added()

        if self.datetime is None:
            raise ValueError("Datetime must be set.")
        if not isinstance(self.datetime, _datetime):
            raise ValueError("Datetime must be an instance of datetime.")

        self.datetime = self.datetime + timedelta(seconds=self.delay_for_seconds,
                                                  minutes=self.delay_for_minutes,
                                                  hours=self.delay_for_hours,
                                                  days=self.delay_for_days)

    def check(self) -> bool:
        if self.task.last_run is None:
                return True
        return False


class _AtPredefinedDatetime(AtDatetime):
    def __init__(self,
                 delay_for_seconds: int = 0,
                 delay_for_minutes: int = 0,
                 delay_for_hours: int = 0,
                 delay_for_days: int = 0):
        super().__init__(delay_for_seconds=delay_for_seconds,
                         delay_for_minutes=delay_for_minutes,
                         delay_for_hours=delay_for_hours,
                         delay_for_days=delay_for_days)


class AtNow(_AtPredefinedDatetime):
    def manager_added(self) -> None:
        self.datetime = _datetime.now()
        super().manager_added()


class AtManagerCreation(AtDatetime):
    def manager_added(self) -> None:
        self.datetime = self.task.manager.creation_time
        super().manager_added()


class AtManagerStart(AtDatetime):
    def manager_added(self) -> None:
        self.datetime = self.task.manager.start_time
        super().manager_added()
