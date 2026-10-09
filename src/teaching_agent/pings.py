"""Unprompted-ping scheduling: N random times per day inside a waking window.

Deterministic per (date, count, window): a restart redraws the SAME day, so a
slot can't be skipped or doubled by a crash; the state file's ``last_fired``
guards against firing one slot twice. The count is learner-tunable live via
``/pings`` — a count change redraws the day, which can shift the remaining
slots (documented, accepted: the learner asked, the day reshuffles).

Pedagogy lives in the tick prompt (engine) and the knowledge base; this module
is plumbing: WHEN to wake the teacher, never WHAT to say.
"""

from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

_MIN_GAP = timedelta(minutes=45)
_MAX_ATTEMPTS = 2_000


@dataclass(frozen=True, slots=True)
class _State:
    pings_per_day: int
    last_fired: datetime | None


class PingController:
    """Owns data/pings.json and the daily random schedule."""

    def __init__(
        self,
        state_file: Path,
        *,
        window_start_hour: int = 8,
        window_end_hour: int = 23,
        default_count: int = 3,
    ) -> None:
        if not 0 <= window_start_hour < window_end_hour <= 24:
            raise ValueError("ping window must satisfy 0 <= start < end <= 24")
        self._state_file = state_file
        self._window_start = time(window_start_hour)
        self._window_end = time(window_end_hour, 0) if window_end_hour < 24 else time(23, 59, 59)
        self._end_exclusive = window_end_hour == 24
        self._default_count = default_count

    # -- state ----------------------------------------------------------

    def _load(self) -> _State:
        try:
            raw = json.loads(self._state_file.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return _State(pings_per_day=self._default_count, last_fired=None)
        count = raw.get("pings_per_day", self._default_count)
        last = raw.get("last_fired")
        try:
            last_fired = datetime.fromisoformat(last) if last else None
        except (TypeError, ValueError):
            last_fired = None
        return _State(pings_per_day=max(0, int(count)), last_fired=last_fired)

    def _save(self, state: _State) -> None:
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "pings_per_day": state.pings_per_day,
            "last_fired": state.last_fired.isoformat() if state.last_fired else None,
        }
        tmp = self._state_file.with_suffix(self._state_file.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(self._state_file)

    def count(self) -> int:
        """Pings per day; 0 = off. Read live so /pings applies without restart."""
        return self._load().pings_per_day

    def set_count(self, count: int) -> None:
        if count < 0:
            raise ValueError("pings per day must be >= 0")
        state = self._load()
        self._save(_State(pings_per_day=count, last_fired=state.last_fired))

    # -- schedule ---------------------------------------------------------

    def slots_for(self, day: date, count: int | None = None) -> list[datetime]:
        """The day's fire times: random, sorted, >=45 min apart, in-window.

        Deterministic per (day, count, window) so restarts are safe.
        """
        n = self.count() if count is None else count
        if n <= 0:
            return []
        rng = random.Random(
            f"{day.isoformat()}|{n}|{self._window_start}|{self._window_end}"
        )
        start = datetime.combine(day, self._window_start)
        end = datetime.combine(day, self._window_end)
        span = (end - start).total_seconds()
        if span <= 0:
            return []
        gap = _MIN_GAP
        # If the window can't fit n slots at the standard gap, shrink the
        # gap rather than drop slots (the learner asked for n).
        while gap > timedelta(minutes=5) and (n - 1) * gap >= timedelta(seconds=span):
            gap /= 2
        for _ in range(_MAX_ATTEMPTS):
            draws = sorted(start + timedelta(seconds=rng.uniform(0, span)) for _ in range(n))
            if all(b - a >= gap for a, b in zip(draws, draws[1:], strict=False)):
                return draws
        # Deterministic fallback: even spacing (only reachable in absurd configs).
        step = span / n
        return [start + timedelta(seconds=step * (i + 0.5)) for i in range(n)]

    def due(self, now: datetime | None = None) -> bool:
        """A slot has passed and not been fired. Missed slots collapse to ONE
        catch-up ping (the latest), not a backlog of nags."""
        now = now or datetime.now()
        state = self._load()
        if state.pings_per_day <= 0:
            return False
        for slot in reversed(self.slots_for(now.date(), state.pings_per_day)):
            if slot <= now and (state.last_fired is None or slot > state.last_fired):
                return True
        return False

    def mark_fired(self, when: datetime | None = None) -> None:
        state = self._load()
        self._save(
            _State(pings_per_day=state.pings_per_day, last_fired=when or datetime.now())
        )

    def next_fire(self, now: datetime | None = None) -> datetime | None:
        """Next slot to wait for; None when pings are off."""
        now = now or datetime.now()
        count = self.count()
        if count <= 0:
            return None
        for slot in self.slots_for(now.date(), count):
            if slot > now:
                return slot
        tomorrow = self.slots_for(now.date() + timedelta(days=1), count)
        return tomorrow[0] if tomorrow else None

    def describe(self, now: datetime | None = None) -> str:
        now = now or datetime.now()
        count = self.count()
        if count <= 0:
            return "Pings are OFF (/pings <n> to resume, e.g. /pings 3)."
        remaining = [s for s in self.slots_for(now.date(), count) if s > now]
        times = ", ".join(s.strftime("%H:%M") for s in remaining) or "none left today"
        window = f"{self._window_start:%H:%M}\u2013{self._window_end:%H:%M}"
        return f"Pings: {count}/day, window {window}. Remaining today: {times}."
