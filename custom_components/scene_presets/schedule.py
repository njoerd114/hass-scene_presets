from __future__ import annotations

from datetime import datetime

DEFAULT_TIME = "00:00"


def _parse_time(value: object) -> tuple[int, int]:
    hour, _, minute = str(value).partition(":")
    try:
        return int(hour), int(minute)
    except ValueError:
        return -1, -1


def _weekday_matches(days, now: datetime) -> bool:
    if not days:
        return True

    short = now.strftime("%a").lower()[:3]
    return short in {str(day).lower()[:3] for day in days}


def fired_key(entry: dict, now: datetime) -> str:
    return f"{entry.get('id')}:{now.date().isoformat()}"


def due_entries(schedules: list[dict], now: datetime, fired: set[str]) -> list[dict]:
    due = []

    for entry in schedules:
        if fired_key(entry, now) in fired:
            continue

        hour, minute = _parse_time(entry.get("time", DEFAULT_TIME))
        if hour == now.hour and minute == now.minute and _weekday_matches(entry.get("days"), now):
            due.append(entry)

    return due
