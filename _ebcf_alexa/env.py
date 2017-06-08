import datetime
from pytz import utc as UTC, timezone

TZ = timezone('US/Pacific')


def now() -> datetime.datetime:
    return datetime.datetime.now(tz=UTC)


def localnow() -> datetime.datetime:
    return now().astimezone(TZ)


def date() -> datetime.date:
    return now().date()


def localdate() -> datetime.date:
    return localnow().date()
