# tzmeet

Finding a meeting time across timezones usually means staring at a
converter and doing the arithmetic by hand. `tzmeet` does it for you:
give it a date and each person's working hours in their own timezone,
and it lists every slot of the requested length that fits everyone,
in UTC and in each person's local time.

Working windows are anchored to the date *in each participant's own
timezone*, so daylight-saving transitions are handled automatically
(British Summer Time shifts London's window by an hour between summer
and winter, for example).

## Install

```bash
pip install .
```

Requires Python 3.10+. No dependencies (standard library only).

## Usage

Create an input file:

```json
{
  "date": "2026-11-10",
  "duration_minutes": 60,
  "step_minutes": 30,
  "participants": [
    {"name": "Paso", "tz": "Asia/Tokyo", "start": "09:00", "end": "18:00"},
    {"name": "Bob", "tz": "Europe/London", "start": "08:00", "end": "17:00"}
  ]
}
```

Then run:

```bash
tzmeet input.json
# 1 slot(s) on 2026-11-10 (duration 1:00:00):
#   UTC 08:00  |  Paso 17:00  Bob 08:00
```

`start` and `end` default to `09:00` and `17:00`; `duration_minutes`
defaults to 60 and `step_minutes` to 30. Overnight windows (end before
start) are not supported.

Exit status: 0 when at least one slot is found, 1 when no window fits
everyone, 2 on unreadable or invalid input — so it can be used in
scripts.

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## License

MIT. See [LICENSE](LICENSE).
