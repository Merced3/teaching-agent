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
from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

_MIN_GAP = timedelta(minutes=45)
_MAX_ATTEMPTS = 2_000


@dataclass(frozen=True, slots=True)
class _State:
    pings_per_day: int
    last_fired: datetime | None
    # None = fall back to the constructor (env) hours, like the count does.
    window_start_hour: int | None = None
    window_end_hour: int | None = None


class PingController:
    """Owns data/pings.json and the daily random schedule."""

    def __init__(
        self,
        state_file: Path,
        *,
        window_start_hour: int = 8,
        window_end_hour: int = 22,
        default_count: int = 3,
        timezone_name: str = "America/Chicago",
    ) -> None:
        if not 0 <= window_start_hour < window_end_hour <= 24:
            raise ValueError("ping window must satisfy 0 <= start < end <= 24")
        self._state_file = state_file
        # Constructor hours are boot defaults only; /pings window overrides
        # them live via the state file (same pattern as the count).
        self._env_start_hour = window_start_hour
        self._env_end_hour = window_end_hour
        self._default_count = default_count
        # The window and "now" live in the LEARNER's timezone, not the
        # server's — the VPS runs on UTC, which would shift the waking
        # window by 5–6 hours (decision-log 2026-10-09, tz fix).
        self._tz = ZoneInfo(timezone_name)

    def _now(self) -> datetime:
        """Current time in the learner's timezone, naive.

        Everything in this module (slots, last_fired) is naive local time,
        so the schedule is defined by wall-clock in ``self._tz`` regardless
        of the host's clock. Naive-on-purpose: mixing aware and naive
        datetimes would break every comparison here.
        """
        return datetime.now(self._tz).replace(tzinfo=None)

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
        return _State(
            pings_per_day=max(0, int(count)),
            last_fired=last_fired,
            window_start_hour=raw.get("window_start_hour"),
            window_end_hour=raw.get("window_end_hour"),
        )

    def _save(self, state: _State) -> None:
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "pings_per_day": state.pings_per_day,
            "window_start_hour": state.window_start_hour,
            "window_end_hour": state.window_end_hour,
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
        self._save(replace(state, pings_per_day=count))

    # -- window -----------------------------------------------------------

    def _window(self) -> tuple[time, time]:
        """The live waking window (state file wins over env defaults)."""
        state = self._load()
        start_hour = state.window_start_hour
        end_hour = state.window_end_hour
        if start_hour is None or end_hour is None or not 0 <= start_hour < end_hour <= 24:
            start_hour, end_hour = self._env_start_hour, self._env_end_hour
        start = time(start_hour)
        end = time(end_hour, 0) if end_hour < 24 else time(23, 59, 59)
        return start, end

    def window(self) -> tuple[int, int]:
        """The live window as (start_hour, end_hour), for display."""
        start, end = self._window()
        return start.hour, end.hour

    def set_window(self, start_hour: int, end_hour: int) -> None:
        """Live-retune the waking window; redraws today's remaining slots
        (same accepted reshuffle semantics as a count change)."""
        if not 0 <= start_hour < end_hour <= 24:
            raise ValueError("ping window must satisfy 0 <= start < end <= 24")
        state = self._load()
        self._save(replace(state, window_start_hour=start_hour, window_end_hour=end_hour))

    # -- schedule ---------------------------------------------------------

    def slots_for(self, day: date, count: int | None = None) -> list[datetime]:
        """The day's fire times: random, sorted, >=45 min apart, in-window.

        Deterministic per (day, count, window) so restarts are safe.
        """
        n = self.count() if count is None else count
        if n <= 0:
            return []
        window_start, window_end = self._window()
        rng = random.Random(f"{day.isoformat()}|{n}|{window_start}|{window_end}")
        start = datetime.combine(day, window_start)
        end = datetime.combine(day, window_end)
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
        now = now or self._now()
        state = self._load()
        if state.pings_per_day <= 0:
            return False
        for slot in reversed(self.slots_for(now.date(), state.pings_per_day)):
            if slot <= now and (state.last_fired is None or slot > state.last_fired):
                return True
        return False

    def mark_fired(self, when: datetime | None = None) -> None:
        state = self._load()
        self._save(_State(pings_per_day=state.pings_per_day, last_fired=when or self._now()))

    def next_fire(self, now: datetime | None = None) -> datetime | None:
        """Next slot to wait for; None when pings are off."""
        now = now or self._now()
        count = self.count()
        if count <= 0:
            return None
        for slot in self.slots_for(now.date(), count):
            if slot > now:
                return slot
        tomorrow = self.slots_for(now.date() + timedelta(days=1), count)
        return tomorrow[0] if tomorrow else None

    def describe(self, now: datetime | None = None) -> str:
        now = now or self._now()
        count = self.count()
        if count <= 0:
            return "Pings are OFF (/pings <n> to resume, e.g. /pings 3)."
        remaining = [s for s in self.slots_for(now.date(), count) if s > now]
        times = ", ".join(s.strftime("%H:%M") for s in remaining) or "none left today"
        window_start, window_end = self._window()
        window = f"{window_start:%H:%M}\u2013{window_end:%H:%M}"
        return (
            f"Pings: {count}/day, window {window} {self._tz.key}. "
            f"Remaining today: {times}."
        )
