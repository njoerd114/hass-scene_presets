from datetime import datetime

from scene_presets.schedule import due_entries, fired_key


def test_entry_is_due_at_matching_time():
    now = datetime(2026, 6, 1, 7, 30)
    schedules = [{"id": "a", "time": "07:30", "preset_id": "p"}]

    assert due_entries(schedules, now, set()) == schedules


def test_entry_is_not_due_at_other_time():
    now = datetime(2026, 6, 1, 8, 0)

    assert due_entries([{"id": "a", "time": "07:30"}], now, set()) == []


def test_weekday_filter_matches():
    now = datetime(2026, 6, 1, 7, 30)

    assert due_entries([{"id": "a", "time": "07:30", "days": ["Mon"]}], now, set())
    assert due_entries([{"id": "a", "time": "07:30", "days": ["Tue"]}], now, set()) == []


def test_fired_key_prevents_refire():
    now = datetime(2026, 6, 1, 7, 30)
    schedules = [{"id": "a", "time": "07:30"}]
    fired = {fired_key(schedules[0], now)}

    assert due_entries(schedules, now, fired) == []


def test_invalid_time_is_never_due():
    now = datetime(2026, 6, 1, 7, 30)

    assert due_entries([{"id": "a", "time": "nonsense"}], now, set()) == []
