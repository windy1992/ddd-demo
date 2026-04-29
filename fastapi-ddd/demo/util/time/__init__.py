# coding: utf-8
from datetime import datetime, timedelta, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_after_hours(hours: int) -> datetime:
    return utc_now() + timedelta(hours=hours)
