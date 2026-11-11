from datetime import datetime, timezone, timedelta
from typing import Union


class Clock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class FakeClock(Clock):
    def __init__(self, fixed: datetime):
        if fixed.tzinfo is None:
            self._fixed = fixed.replace(tzinfo=timezone.utc)
        else:
            self._fixed = fixed.astimezone(timezone.utc)

    def now(self) -> datetime:
        return self._fixed

    def advance(self, **kwargs) -> None:
        self._fixed = self._fixed + timedelta(**kwargs)


_default_clock = Clock()


def get_clock() -> Clock:
    return _default_clock


def set_clock(clock: Clock) -> None:
    global _default_clock
    _default_clock = clock


def now() -> datetime:
    return _default_clock.now()


def format_timestamp(dt: datetime) -> str:
    """Format datetime to UTC 'YYYY-MM-DD HH:MM:SS' format."""
    if dt.tzinfo is not None:
        utc_dt = dt.astimezone(timezone.utc)
    else:
        utc_dt = dt.replace(tzinfo=timezone.utc)
    return utc_dt.strftime("%Y-%m-%d %H:%M:%S")


def parse_timestamp(s: str) -> datetime:
    """Parse 'YYYY-MM-DD HH:MM:SS' format into UTC-aware datetime."""
    dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    return dt.replace(tzinfo=timezone.utc)

