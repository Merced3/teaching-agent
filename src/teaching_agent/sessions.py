"""Session registry: pi sessions as agnostic, state-managed resources.

Decision log 2026-10-06 ("Voice TTS root-caused; session architecture
decided") is the spec:

- A session is created knowing nothing — no type, no owner — and is typed
  after the fact by whatever fills it (a lesson, general chat, a lecture).
- Lifecycle is persisted: OPEN -> CLOSING -> COMPLETE. OPEN survives
  crash/restart (its owner reattaches on boot); CLOSING is resumed on boot
  only to finish the close checklist, then marked COMPLETE; COMPLETE is
  immutable and never accepts turns again.
- A lesson owns its session id for the lesson's lifetime only. Revisiting
  a CLOSED lesson never resumes its transcript — files are long-term
  memory; sessions are working memory (thesis corollary, 2026-10-06).
- Orphaned OPEN sessions (owner gone, or ancient) age out to COMPLETE.

Like the lesson binding, this is operational state: it lives under data/
and never in the knowledge base.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

logger = logging.getLogger(__name__)

OPEN = "OPEN"
CLOSING = "CLOSING"
COMPLETE = "COMPLETE"

MAIN_OWNER = "main"


def lesson_owner(thread_id: int) -> str:
    return f"lesson:{thread_id}"


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


@dataclass(slots=True)
class SessionRecord:
    id: str
    state: str
    owner: str | None
    session_file: str | None
    created_at: str
    closed_at: str | None = None
    turns: int = 0
    cost_usd: float = 0.0


@dataclass(slots=True)
class BootScan:
    """What a boot found: sessions to finish closing, and live OPEN ones."""

    closing: list[SessionRecord]
    open: list[SessionRecord]


class SessionRegistry:
    """Owns the persisted lifecycle of every pi session this agent creates."""

    def __init__(self, state_file: Path) -> None:
        self._state_file = state_file
        self._records: dict[str, SessionRecord] = {}
        self._load()

    def all(self) -> list[SessionRecord]:
        return list(self._records.values())

    def get(self, record_id: str) -> SessionRecord | None:
        return self._records.get(record_id)

    def find_by_owner(self, owner: str) -> SessionRecord | None:
        """The newest OPEN session owned by `owner`, if any."""
        owned = [
            r for r in self._records.values()
            if r.state == OPEN and r.owner == owner
        ]
        return max(owned, key=lambda r: r.created_at) if owned else None

    def create(self, *, session_file: str | None, owner: str | None) -> SessionRecord:
        record = SessionRecord(
            id=uuid4().hex[:12],
            state=OPEN,
            owner=owner,
            session_file=session_file,
            created_at=_now(),
        )
        self._records[record.id] = record
        self._save()
        logger.info("Session %s registered (%s, owner=%s).", record.id, OPEN, owner)
        return record

    def touch(
        self, record_id: str, *, session_file: str | None, cost: float
    ) -> None:
        """Record a completed turn: session file (late-binding), count, spend."""
        record = self._records[record_id]
        if session_file:
            record.session_file = session_file
        record.turns += 1
        record.cost_usd += cost
        self._save()

    def reassign(self, record_id: str, owner: str) -> None:
        """Type a session after the fact — e.g. a fresh main session that a
        lesson just claimed for its lifetime."""
        self._records[record_id].owner = owner
        self._save()

    def mark_closing(self, record_id: str) -> None:
        self._records[record_id].state = CLOSING
        self._save()

    def mark_complete(self, record_id: str) -> None:
        record = self._records[record_id]
        record.state = COMPLETE
        record.closed_at = _now()
        self._save()
        logger.info("Session %s COMPLETE (%s turns, $%.4f).",
                    record.id, record.turns, record.cost_usd)

    def boot_scan(
        self, *, orphan_days: int, active_lesson_thread: int | None
    ) -> BootScan:
        """Classify persisted sessions at process start.

        - CLOSING records are returned for the engine to finish the close
          checklist (the caller marks them COMPLETE afterward).
        - OPEN records whose owner is a lesson other than the currently
          active one, or with no owner older than `orphan_days`, are
          orphaned: aged out to COMPLETE immediately — a dead owner must
          not resurrect a stale working memory.
        - Everything else is returned OPEN for the owner to reattach.
        """
        closing: list[SessionRecord] = []
        live: list[SessionRecord] = []
        now = datetime.now(UTC)
        for record in self._records.values():
            if record.state == CLOSING:
                closing.append(record)
            elif record.state == OPEN:
                if self._is_orphan(record, active_lesson_thread, now, orphan_days):
                    logger.info("Session %s orphaned (owner=%s); aging out.",
                                record.id, record.owner)
                    self.mark_complete(record.id)
                else:
                    live.append(record)
        if closing or live:
            self._save()
        return BootScan(closing=closing, open=live)

    @staticmethod
    def _is_orphan(
        record: SessionRecord,
        active_lesson_thread: int | None,
        now: datetime,
        orphan_days: int,
    ) -> bool:
        owner = record.owner
        if owner is not None and owner.startswith("lesson:"):
            return owner != lesson_owner(active_lesson_thread or -1)
        if owner is None:
            try:
                created = datetime.fromisoformat(record.created_at)
            except ValueError:
                return True
            return (now - created).days >= orphan_days
        return False

    def _load(self) -> None:
        try:
            raw = json.loads(self._state_file.read_text(encoding="utf-8"))
            for item in raw:
                record = SessionRecord(**item)
                self._records[record.id] = record
            logger.info("Session registry loaded: %d record(s).", len(self._records))
        except (OSError, ValueError, TypeError, KeyError):
            self._records = {}

    def _save(self) -> None:
        try:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            self._state_file.write_text(
                json.dumps([asdict(r) for r in self._records.values()], indent=2),
                encoding="utf-8",
            )
        except OSError:
            logger.warning("Session registry save failed.", exc_info=True)
