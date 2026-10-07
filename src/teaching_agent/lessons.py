"""Lesson threads: pi decides lesson boundaries; this module transports them.

Pi marks lesson events with directive lines anywhere in its reply (taught
via the system prompt's channel rules):

    [lesson: start | State machines]
    [lesson: milestone | guarded writes recalled unaided]

Closing is deliberately NOT a directive. A lesson ends only when the human
runs /lesson end (decision log 2026-10-07): an end boundary is destructive
(clears the thread binding mid-conversation, freezing the session and
diverting the reply to main), and pi's boundary detection is probabilistic —
the same reason /lesson commands exist as the deterministic backstop
(2026-10-02). A stray [lesson: end] line is stripped but ignored.

The engine strips those lines before the reply is posted or spoken, and
this module does the Discord-side work: one thread per lesson named after
the topic, milestones in the main channel (started / learned / complete),
and the active thread remembered so voice transcripts land in the thread
instead of flooding the main channel. Raw transcripts are exhaust;
milestones are the product (decision log, 2026-10-02).

The active lesson survives restarts via a small JSON state file — a lesson
can span days, and the binding is operational state, not knowledge, so it
lives under data/ and never in the knowledge base.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from .hub_client import HubClient

logger = logging.getLogger(__name__)

_DIRECTIVE = re.compile(
    r"^\[lesson:\s*(start|milestone|end)\s*(?:\|\s*(.*?)\s*)?\]$", re.IGNORECASE
)


class LessonManager:
    """Owns the active lesson thread and the main-channel milestone posts."""

    def __init__(
        self,
        hub: HubClient,
        channel_id: int,
        state_file: Path,
        on_boundary: Callable[[str, int | None], Awaitable[Any]] | None = None,
    ) -> None:
        self._hub = hub
        self._channel_id = channel_id
        self._state_file = state_file
        # Session-architecture hook (decision log 2026-10-06): the engine
        # owns pi session lifecycles; lesson start/end are the boundaries
        # that re-type or rotate them. Pure transport here — the callback
        # is the engine's seam.
        self._on_boundary = on_boundary
        self._thread_id: int | None = None
        self._topic: str | None = None
        self._load()

    @property
    def thread_id(self) -> int | None:
        """Where lesson exhaust (voice transcripts) goes; None = main channel."""
        return self._thread_id

    @property
    def topic(self) -> str | None:
        return self._topic

    async def process(self, reply: str) -> str:
        """Execute any lesson directives in a pi reply; return the stripped text."""
        kept: list[str] = []
        for line in reply.splitlines():
            match = _DIRECTIVE.match(line.strip())
            if match is None:
                kept.append(line)
                continue
            action, detail = match.group(1).lower(), (match.group(2) or "").strip()
            try:
                await self._execute(action, detail)
            except Exception:
                logger.exception("Lesson directive failed: %s", line.strip())
        return "\n".join(kept).strip()

    async def start(self, topic: str) -> str:
        """Open a lesson thread. Returns a human-readable confirmation."""
        if self._thread_id is not None:
            await self._post_milestone(
                f"✅ **Lesson complete: {self._topic}** — superseded by a new lesson."
            )
        thread = await self._hub.create_thread(self._channel_id, topic)
        self._thread_id = int(thread["id"])
        self._topic = topic
        self._save()
        await self._post_milestone(
            f"📘 **Lesson started: {topic}** — the running record lives in the thread."
        )
        logger.info("Lesson started: %r (thread %s).", topic, self._thread_id)
        await self._notify_boundary("start", self._thread_id)
        return f"Lesson started: **{topic}** — transcripts and the record go to the thread."

    async def end(self, summary: str = "") -> str:
        """Close the active lesson. Returns a human-readable confirmation."""
        if self._thread_id is None:
            return "No active lesson."
        topic = self._topic or "lesson"
        suffix = f" — {summary}" if summary else ""
        await self._post_milestone(f"✅ **Lesson complete: {topic}**{suffix}")
        self._thread_id = None
        self._topic = None
        self._save()
        logger.info("Lesson ended: %r.", topic)
        await self._notify_boundary("end", None)
        return f"Lesson complete: **{topic}**."

    def describe(self) -> str:
        if self._thread_id is None:
            return "No active lesson."
        return f"Active lesson: **{self._topic}** (thread {self._thread_id})."

    async def _execute(self, action: str, detail: str) -> None:
        if action == "start":
            if not detail:
                logger.warning("Lesson start without a topic; ignored.")
                return
            await self.start(detail)
        elif action == "milestone":
            label = f"**{self._topic}:** " if self._topic else ""
            await self._post_milestone(f"📍 {label}{detail or '(milestone)'}")
        elif action == "end":
            # Human-only boundary: stripped above so the learner never sees
            # it, deliberately not executed. The prompt teaches pi to ask
            # for /lesson end instead.
            logger.info("Ignored pi [lesson: end] directive (close is human-only).")

    async def _post_milestone(self, text: str) -> None:
        from .hub_client import HubError

        try:
            await self._hub.post_message(self._channel_id, text)
        except HubError:
            logger.warning("Milestone post failed: %.60s", text, exc_info=True)

    async def _notify_boundary(self, event: str, thread_id: int | None) -> None:
        if self._on_boundary is None:
            return
        try:
            await self._on_boundary(event, thread_id)
        except Exception:
            logger.exception("Lesson boundary hook failed: %s", event)

    def _load(self) -> None:
        try:
            data = json.loads(self._state_file.read_text(encoding="utf-8"))
            self._thread_id = int(data["thread_id"])
            self._topic = str(data.get("topic") or "") or None
            logger.info(
                "Resumed active lesson %r (thread %s).", self._topic, self._thread_id
            )
        except (OSError, ValueError, KeyError, TypeError):
            self._thread_id = None
            self._topic = None

    def _save(self) -> None:
        try:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            if self._thread_id is None:
                self._state_file.unlink(missing_ok=True)
            else:
                self._state_file.write_text(
                    json.dumps({"thread_id": self._thread_id, "topic": self._topic}),
                    encoding="utf-8",
                )
        except OSError:
            logger.warning("Lesson state save failed.", exc_info=True)
