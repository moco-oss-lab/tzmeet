import unittest
from datetime import date, datetime, timedelta, timezone

from tzmeet.core import Participant, find_slots


def utc(day, hour, minute=0):
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=timezone.utc)


class TestTzmeet(unittest.TestCase):
    def test_tokyo_london_overlap_november(self):
        # November: London is on GMT (UTC+0), Tokyo UTC+9.
        # Tokyo 09:00-18:00 -> 00:00-09:00 UTC; London 08:00-17:00 -> 08:00-17:00 UTC.
        day = date(2026, 11, 10)
        slots = find_slots(
            [
                Participant("Paso", "Asia/Tokyo", "09:00", "18:00"),
                Participant("Bob", "Europe/London", "08:00", "17:00"),
            ],
            day,
        )
        self.assertEqual(slots, [utc(day, 8)])

    def test_tokyo_lima_no_overlap(self):
        # Tokyo 09:00-18:00 -> 00:00-09:00 UTC; Lima (UTC-5) 09:00-17:00 -> 14:00-22:00 UTC.
        day = date(2026, 11, 10)
        slots = find_slots(
            [
                Participant("Paso", "Asia/Tokyo", "09:00", "18:00"),
                Participant("Ana", "America/Lima", "09:00", "17:00"),
            ],
            day,
        )
        self.assertEqual(slots, [])

    def test_daylight_saving_changes_london_window(self):
        # July: London is on BST (UTC+1), so 08:00-17:00 local -> 07:00-16:00 UTC.
        day = date(2026, 7, 10)
        slots = find_slots(
            [
                Participant("Paso", "Asia/Tokyo", "09:00", "18:00"),
                Participant("Bob", "Europe/London", "08:00", "17:00"),
            ],
            day,
        )
        self.assertEqual(slots, [utc(day, 7), utc(day, 7, 30), utc(day, 8)])

    def test_duration_and_step_respected(self):
        day = date(2026, 11, 10)
        slots = find_slots(
            [Participant("A", "UTC", "09:00", "12:00")],
            day,
            duration=timedelta(minutes=90),
            step=timedelta(minutes=60),
        )
        self.assertEqual(slots, [utc(day, 9), utc(day, 10)])

    def test_unknown_timezone_raises(self):
        with self.assertRaises(Exception):
            find_slots([Participant("X", "Mars/Olympus")], date(2026, 11, 10))

    def test_end_before_start_raises(self):
        with self.assertRaises(ValueError):
            find_slots([Participant("X", "UTC", "17:00", "09:00")], date(2026, 11, 10))

    def test_empty_participants_raises(self):
        with self.assertRaises(ValueError):
            find_slots([], date(2026, 11, 10))


if __name__ == "__main__":
    unittest.main()
