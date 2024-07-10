from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional


class Trigger(ABC):
    def __init__(self):
        self.manager = None

    @abstractmethod
    def init(self, manager):
        ...

    @abstractmethod
    def next(self, *args, **kwargs) -> datetime:
        ...


class Interval(Trigger):
    def __init__(self,
                 seconds: int = 0,
                 minutes: int = 0,
                 hours: int = 0,
                 days: int = 0,
                 weeks: int = 0,
                 months: int = 0,
                 years: int = 0):
        super().__init__()

        self.interval: Optional[int] = None
        self.seconds: int = seconds
        self.minutes: int = minutes
        self.hours: int = hours
        self.days: int = days
        self.weeks: int = weeks
        self.months: int = months
        self.years: int = years

    def init(self, manager):
        self.manager = manager

        # calculate interval in seconds
        self.interval = self.seconds
        self.interval += self.minutes * 60
        self.interval += self.hours * 60 * 60
        self.interval += self.days * 60 * 60 * 24
        self.interval += self.weeks * 60 * 60 * 24 * 7
        self.interval += self.months * 60 * 60 * 24 * 30
        self.interval += self.years * 60 * 60 * 24 * 365

    def __str__(self):
        interval = self.interval
        interval_str = "Every "
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
        interval_str = interval_str.strip()
        return interval_str

    def __int__(self):
        return self.interval

    def __add__(self, other):
        if isinstance(other, (Interval, int, float)):
            return Interval(seconds=int(self) + int(other))
        else:
            raise ValueError(f"Can't add Interval and '{type(other)}'.")

    def next(self, last: datetime) -> datetime:
        return last + timedelta(seconds=int(self))


class EverySeconds(Interval):
    def __init__(self, seconds: int):
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
                 year: Optional[int] = None,
                 delay_for_seconds: int = 0,
                 delay_for_minutes: int = 0,
                 delay_for_hours: int = 0,
                 delay_for_days: int = 0):
        super().__init__()

        self.second: Optional[int] = second
        self.minute: Optional[int] = minute
        self.hour: Optional[int] = hour
        self.day: Optional[int] = day
        self.month: Optional[int] = month
        self.year: Optional[int] = year
        self.delay_for_seconds: int = delay_for_seconds
        self.delay_for_minutes: int = delay_for_minutes
        self.delay_for_hours: int = delay_for_hours
        self.delay_for_days: int = delay_for_days

    def init(self, manager):
        self.manager = manager

        # check if some of the values are set
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
            if at_str:
                at_str += "and "
            at_str += f"month {self.month:02} "
        if self.day is not None:
            if at_str:
                at_str += "and "
            at_str += f"day {self.day:02} "
        if self.hour is not None:
            if at_str:
                at_str += "and "
            at_str += f"hour {self.hour:02} "
        if self.minute is not None:
            if at_str:
                at_str += "and "
            at_str += f"minute {self.minute:02} "
        if self.second is not None:
            if at_str:
                at_str += "and "
            at_str += f"second {self.second:02} "
        at_str = at_str.strip()
        return at_str

    def next(self) -> datetime:
        n = datetime.now().replace(microsecond=0)
        second = 0
        if self.second is not None:
            second = self.second
            second_n = n.replace(second=second)
            if second_n < n:
                n += timedelta(minutes=1)
            n = n.replace(second=second)
        minute = 0
        if self.minute is not None:
            minute = self.minute
            minute_n = n.replace(minute=minute)
            if minute_n < n:
                n += timedelta(hours=1)
            n = n.replace(minute=minute, second=second)
        hour = 0
        if self.hour is not None:
            hour = self.hour
            hour_n = n.replace(hour=hour)
            if hour_n < n:
                n += timedelta(days=1)
            n = n.replace(hour=hour, minute=minute, second=second)
        day = 1
        if self.day is not None:
            day = self.day
            day_n = n.replace(day=day)
            if day_n < n:
                while True:
                    n += timedelta(days=1)
                    if n.day == day:
                        break
            n = n.replace(day=day, hour=hour, minute=minute, second=second)
        month = 1
        if self.month is not None:
            month = self.month
            month_n = n.replace(month=month)
            if month_n < n:
                while True:
                    n += timedelta(days=1)
                    if n.month == month:
                        break
            n = n.replace(month=month, day=day, hour=hour, minute=minute, second=second)
        if self.year is not None:
            n = n.replace(year=self.year, month=month, day=day, hour=hour, minute=minute, second=second)

        return n


class AtNow(At):
    def init(self, manager):
        self.manager = manager

        now = datetime.now() + timedelta(seconds=self.delay_for_seconds,
                                         minutes=self.delay_for_minutes,
                                         hours=self.delay_for_hours,
                                         days=self.delay_for_days)
        self.second = now.second
        self.minute = now.minute
        self.hour = now.hour
        self.day = now.day
        self.month = now.month
        self.year = now.year

        super().init(manager)


class AtCreation(At):
    def init(self, manager):
        self.manager = manager

        creation_time = self.manager.creation_time + timedelta(seconds=self.delay_for_seconds,
                                                               minutes=self.delay_for_minutes,
                                                               hours=self.delay_for_hours,
                                                               days=self.delay_for_days)
        self.second = creation_time.second
        self.minute = creation_time.minute
        self.hour = creation_time.hour
        self.day = creation_time.day
        self.month = creation_time.month
        self.year = creation_time.year

        super().init(manager)
