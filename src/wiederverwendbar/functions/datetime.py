from datetime import datetime, timezone, timedelta


def offset() -> int:
    """
    Calculate the offset between the local time and the UTC time in hours.

    :return: The offset between the local time and the UTC time in hours.
    """

    utc_now = datetime.now(timezone.utc)
    naive_utc_now = datetime(utc_now.year, utc_now.month, utc_now.day, utc_now.hour, utc_now.minute, utc_now.second, utc_now.microsecond)

    delta_seconds = datetime.now().timestamp() - naive_utc_now.timestamp()
    delta_hours = round(delta_seconds // 3600)

    return delta_hours


def local_now() -> datetime:
    """
    Get the current local time.

    :return: The current local time.
    """

    return datetime.now(tz=timezone(timedelta(hours=offset())))
