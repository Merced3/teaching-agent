"""Ping scheduling (pings.py): random N/day slots inside a waking window,
deterministic per date, crash-safe via the state file. Plumbing tests only —
what a ping SAYS lives in the knowledge base, untested here by design."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from teaching_agent.pings import PingController

DAY = datetime(2026, 10, 10).date()


def make_controller(tmp: Path, **kwargs) -> PingController:
    return PingController(tmp / "pings.json", **kwargs)


def test_default_count_when_no_state_file(tmp_path: Path) -> None:
    assert make_controller(tmp_path).count() == 3


def test_set_count_persists_across_instances(tmp_path: Path) -> None:
    make_controller(tmp_path).set_count(5)
    assert make_controller(tmp_path).count() == 5


def test_slots_in_window_sorted_and_spaced(tmp_path: Path) -> None:
    ctl = make_controller(tmp_path, window_start_hour=8, window_end_hour=23)
    slots = ctl.slots_for(DAY, 3)
    assert len(slots) == 3
    assert slots == sorted(slots)
    for slot in slots:
        assert slot.date() == DAY
        assert 8 <= slot.hour < 23
    for a, b in zip(slots, slots[1:], strict=False):
        assert b - a >= timedelta(minutes=45)


def test_slots_deterministic_per_date_and_count(tmp_path: Path) -> None:
    ctl = make_controller(tmp_path)
    assert ctl.slots_for(DAY, 3) == ctl.slots_for(DAY, 3)


def test_slots_differ_across_dates(tmp_path: Path) -> None:
    ctl = make_controller(tmp_path)
    other = DAY + timedelta(days=1)
    assert ctl.slots_for(DAY, 3) != ctl.slots_for(other, 3)


def test_zero_count_means_no_slots(tmp_path: Path) -> None:
    ctl = make_controller(tmp_path)
    assert ctl.slots_for(DAY, 0) == []


def test_due_after_slot_passes(tmp_path: Path) -> None:
    ctl = make_controller(tmp_path, window_start_hour=8, window_end_hour=23)
    first = ctl.slots_for(DAY, 3)[0]
    assert ctl.due(now=first + timedelta(minutes=1)) is True


def test_not_due_before_first_slot(tmp_path: Path) -> None:
    ctl = make_controller(tmp_path, window_start_hour=8, window_end_hour=23)
    first = ctl.slots_for(DAY, 3)[0]
    assert ctl.due(now=first - timedelta(minutes=1)) is False


def test_mark_fired_clears_due(tmp_path: Path) -> None:
    ctl = make_controller(tmp_path, window_start_hour=8, window_end_hour=23)
    first = ctl.slots_for(DAY, 3)[0]
    ctl.mark_fired(first + timedelta(minutes=1))
    assert ctl.due(now=first + timedelta(minutes=2)) is False


def test_missed_slots_collapse_to_one_ping(tmp_path: Path) -> None:
    """After downtime (all slots missed), due fires once, not once per slot."""
    ctl = make_controller(tmp_path, window_start_hour=8, window_end_hour=23)
    end_of_day = datetime.combine(DAY, datetime.max.time()).replace(microsecond=0)
    assert ctl.due(now=end_of_day) is True
    ctl.mark_fired(end_of_day)
    assert ctl.due(now=end_of_day + timedelta(minutes=1)) is False


def test_off_means_never_due_and_no_next_fire(tmp_path: Path) -> None:
    ctl = make_controller(tmp_path)
    ctl.set_count(0)
    assert ctl.due(now=datetime(2026, 10, 10, 12)) is False
    assert ctl.next_fire(now=datetime(2026, 10, 10, 12)) is None


def test_next_fire_rolls_to_tomorrow(tmp_path: Path) -> None:
    ctl = make_controller(tmp_path, window_start_hour=8, window_end_hour=23)
    end_of_day = datetime.combine(DAY, datetime.max.time()).replace(microsecond=0)
    nxt = ctl.next_fire(now=end_of_day)
    assert nxt is not None
    assert nxt.date() == DAY + timedelta(days=1)


def test_next_fire_is_todays_next_slot(tmp_path: Path) -> None:
    ctl = make_controller(tmp_path, window_start_hour=8, window_end_hour=23)
    first, second, _ = ctl.slots_for(DAY, 3)
    assert ctl.next_fire(now=first + timedelta(seconds=1)) == second


def test_describe_reports_count_and_off(tmp_path: Path) -> None:
    ctl = make_controller(tmp_path)
    ctl.set_count(0)
    assert "OFF" in ctl.describe()
    ctl.set_count(4)
    text = ctl.describe(now=datetime(2026, 10, 10, 7, 0))
    assert "4/day" in text


def test_set_window_persists_and_redraws(tmp_path: Path) -> None:
    ctl = make_controller(tmp_path, window_start_hour=8, window_end_hour=22)
    before = ctl.slots_for(DAY, 3)
    ctl.set_window(10, 12)
    assert ctl.window() == (10, 12)
    # Persisted: a fresh instance (simulated restart) sees the new window.
    ctl2 = make_controller(tmp_path, window_start_hour=8, window_end_hour=22)
    assert ctl2.window() == (10, 12)
    after = ctl2.slots_for(DAY, 3)
    assert after != before
    assert all(10 <= s.hour < 12 for s in after)


def test_set_window_rejects_invalid(tmp_path: Path) -> None:
    ctl = make_controller(tmp_path)
    for bad in [(22, 8), (8, 8), (-1, 12), (8, 25)]:
        with pytest.raises(ValueError):
            ctl.set_window(*bad)
    # Window untouched after the rejects.
    assert ctl.window() == (8, 22)
