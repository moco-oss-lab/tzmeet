"""Command line interface for tzmeet.

Input is a JSON file:

    {
      "date": "2026-11-10",
      "duration_minutes": 60,
      "step_minutes": 30,
      "participants": [
        {"name": "Paso", "tz": "Asia/Tokyo", "start": "09:00", "end": "18:00"},
        {"name": "Ana", "tz": "America/Lima", "start": "09:00", "end": "17:00"}
      ]
    }

Exit status: 0 when at least one slot is found, 1 when none is found,
2 on unreadable or invalid input.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .core import Participant, find_slots


def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("top level must be a JSON object")
    return data


def _build(data: dict) -> tuple[list[Participant], date, timedelta, timedelta]:
    try:
        day = date.fromisoformat(data["date"])
    except (KeyError, ValueError) as exc:
        raise ValueError("missing or invalid 'date' (expected YYYY-MM-DD)") from exc

    raw = data.get("participants")
    if not isinstance(raw, list) or not raw:
        raise ValueError("'participants' must be a non-empty list")

    participants = []
    for item in raw:
        if not isinstance(item, dict) or "name" not in item or "tz" not in item:
            raise ValueError("each participant needs 'name' and 'tz'")
        try:
            ZoneInfo(item["tz"])
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"unknown timezone: {item['tz']!r}") from exc
        participants.append(
            Participant(
                name=str(item["name"]),
                tz=str(item["tz"]),
                start=str(item.get("start", "09:00")),
                end=str(item.get("end", "17:00")),
            )
        )

    try:
        duration = timedelta(minutes=int(data.get("duration_minutes", 60)))
        step = timedelta(minutes=int(data.get("step_minutes", 30)))
    except (TypeError, ValueError) as exc:
        raise ValueError("'duration_minutes' and 'step_minutes' must be integers") from exc
    return participants, day, duration, step


def _fmt(dt, tz_name: str) -> str:
    return dt.astimezone(ZoneInfo(tz_name)).strftime("%H:%M")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tzmeet", description="Find meeting windows across timezones."
    )
    parser.add_argument("input", help="JSON file describing participants and date")
    args = parser.parse_args(argv)

    try:
        participants, day, duration, step = _build(_load(args.input))
        slots = find_slots(participants, day, duration, step)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"tzmeet: error: {exc}", file=sys.stderr)
        return 2

    if not slots:
        print(f"No {duration} window fits everyone on {day.isoformat()}.")
        return 1

    print(f"{len(slots)} slot(s) on {day.isoformat()} (duration {duration}):")
    for slot in slots:
        local = "  ".join(f"{p.name} {_fmt(slot, p.tz)}" for p in participants)
        print(f"  UTC {slot.strftime('%H:%M')}  |  {local}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
