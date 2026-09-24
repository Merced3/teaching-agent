"""Black-box tests for the routing boundary: who is answered, and where
replies go. Pedagogy is deliberately untested here — it lives in the
knowledge base, not in code."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

from teaching_agent.config import Settings
from teaching_agent.engine import TeachingEngine
from teaching_agent.pi_rpc import PiRunResult

ENV = {
    "DISCORD_CHANNEL_ID": "100",
    "DISCORD_ALLOWED_USER_ID": "42",
}


def make_engine() -> tuple[TeachingEngine, AsyncMock, AsyncMock]:
    settings = Settings.from_environment(ENV, env_file=None)
    hub = AsyncMock()
    pi = AsyncMock()
    pi.prompt.return_value = PiRunResult(
        text="reply", session_id="s", session_file=None,
        provider="openrouter", model_id="m",
        input_tokens=1, output_tokens=1, cost=0.0,
    )
    return TeachingEngine(settings, hub, pi), hub, pi


def message(text: str, author_id: str = "42", **extra: Any) -> dict[str, Any]:
    return {
        "channel_id": "100",
        "author": {"id": author_id, "name": "learner"},
        "text": text,
        **extra,
    }


async def test_learner_message_is_answered_in_channel() -> None:
    engine, hub, pi = await _started()
    await engine.dispatch(message("teach me"))
    pi.prompt.assert_awaited_once_with("teach me")
    hub.post_message.assert_awaited_once_with(100, "reply")


async def test_strangers_are_ignored() -> None:
    engine, hub, pi = await _started()
    await engine.dispatch(message("hello", author_id="999"))
    pi.prompt.assert_not_awaited()
    hub.post_message.assert_not_awaited()


async def test_thread_messages_reply_into_the_thread() -> None:
    engine, hub, pi = await _started()
    payload = message("hi", thread={"id": "555", "name": "Node 6", "parent_channel_id": "100"})
    await engine.dispatch(payload)
    pi.prompt.assert_awaited_once_with("[thread: Node 6] hi")
    hub.post_message.assert_awaited_once_with(555, "reply")


async def test_recall_tick_silent_means_no_message() -> None:
    engine, hub, pi = await _started()
    pi.prompt.return_value = PiRunResult(
        text="SILENT", session_id="s", session_file=None,
        provider=None, model_id=None, input_tokens=0, output_tokens=0, cost=0.0,
    )
    settings = Settings.from_environment(
        {**ENV, "TEACHING_AGENT_RECALL_PINGS_ENABLED": "true"}, env_file=None
    )
    engine._settings = settings  # noqa: SLF001 — test-only toggle
    await engine.recall_tick()
    hub.post_message.assert_not_awaited()


async def _started() -> tuple[TeachingEngine, AsyncMock, AsyncMock]:
    engine, hub, pi = make_engine()
    return engine, hub, pi
