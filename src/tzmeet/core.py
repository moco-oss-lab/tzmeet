"""Core logic: intersect working hours across timezones for a given date.

All computation is done in UTC. Each participant's working window is
anchored to the requested calendar date *in their own timezone*, so
daylight-saving transitions are handled by zoneinfo automatically.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Participant:
    """One person's working window on a given day.

    ``start`` and ``end`` are local wall-clock times (``"09:00"`` style,
    hours may be given as ``"9"``). ``end`` must be after ``start``;
    overnight windows are not supported.
    """

    name: str
    tz: str
    start: str = "09:00"
    end: str = "17:00"

    def window_utc(self, day: date) -> tuple[datetime, datetime]:
        tz = ZoneInfo(self.tz)
        start = datetime.combine(day, _parse_time(self.start), tzinfo=tz)
        end = datetime.combine(day, _parse_time(self.end), tzinfo=tz)
        if end <= start:
            raise ValueError(
                f"{self.name}: end time {self.end} must be after start time {self.start}"
            )
        return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def _parse_time(text: str) -> time:
    parts = text.strip().split(":")
    if len(parts) == 1:
        hour, minute = int(parts[0]), 0
    elif len(parts) == 2:
        hour, minute = int(parts[0]), int(parts[1])
    else:
        raise ValueError(f"invalid time: {text!r}")
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError(f"invalid time: {text!r}")
    return time(hour, minute)


def find_slots(
    participants: list[Participant],
    day: date,
    duration: timedelta = timedelta(minutes=60),
    step: timedelta = timedelta(minutes=30),
) -> list[datetime]:
    """Return UTC start times of every slot of ``duration`` inside the
    intersection of all participants' working windows on ``day``.

    Slots start on ``step`` boundaries measured from the start of the
    intersection. Raises ValueError on unknown timezones or bad windows.
    """
    if not participants:
        raise ValueError("at least one participant is required")
    if duration <= timedelta(0) or step <= timedelta(0):
        raise ValueError("duration and step must be positive")

    start = end = None
    for person in participants:
        w_start, w_end = person.window_utc(day)
        start = w_start if start is None else max(start, w_start)
        end = w_end if end is None else min(end, w_end)
    assert start is not None and end is not None

    slots: list[datetime] = []
    slot_start = start
    while slot_start + duration <= end:
        slots.append(slot_start)
        slot_start += step
    return slots
