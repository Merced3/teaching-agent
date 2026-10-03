"""Black-box tests for the routing boundary: who is answered, and where
replies go. Pedagogy is deliberately untested here — it lives in the
knowledge base, not in code."""

from __future__ import annotations

from datetime import date
from typing import Any
from unittest.mock import AsyncMock

from teaching_agent.config import Settings
from teaching_agent.engine import TeachingEngine
from teaching_agent.pi_rpc import PiRunResult

ENV = {
    "DISCORD_CHANNEL_ID": "100",
    "DISCORD_ALLOWED_USER_ID": "42",
    "TEACHING_AGENT_NAME": "Alvar",
}


def make_engine(extra_env: dict | None = None) -> tuple[TeachingEngine, AsyncMock, AsyncMock]:
    settings = Settings.from_environment({**ENV, **(extra_env or {})}, env_file=None)
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
    await engine.dispatch(message("Alvar, teach me"))
    pi.prompt.assert_awaited_once_with(f"[date: {date.today().isoformat()}] Alvar, teach me")
    hub.post_message.assert_awaited_once_with(100, "reply")


async def test_unaddressed_message_is_ignored() -> None:
    """The channel doubles as a notepad; only name-addressed messages reply."""
    engine, hub, pi = await _started()
    await engine.dispatch(message("next up is test 2"))
    pi.prompt.assert_not_awaited()
    hub.post_message.assert_not_awaited()


async def test_addressing_is_case_insensitive_word_match() -> None:
    engine, hub, pi = await _started()
    await engine.dispatch(message("hey alvar what do you think?"))
    pi.prompt.assert_awaited_once()
    pi.prompt.reset_mock()
    await engine.dispatch(message("Alvarado is a different word"))
    pi.prompt.assert_not_awaited()


async def test_strangers_are_ignored() -> None:
    engine, hub, pi = await _started()
    await engine.dispatch(message("hello", author_id="999"))
    pi.prompt.assert_not_awaited()
    hub.post_message.assert_not_awaited()


async def test_thread_messages_reply_into_the_thread() -> None:
    engine, hub, pi = await _started()
    payload = message("hi", thread={"id": "555", "name": "Node 6", "parent_channel_id": "100"})
    await engine.dispatch(payload)
    pi.prompt.assert_awaited_once_with(f"[date: {date.today().isoformat()}] [thread: Node 6] hi")
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


def command(name: str, options: dict | None = None, user_id: str = "42") -> dict[str, Any]:
    return {
        "type": "command",
        "interaction_id": "i1",
        "command": name,
        "options": options or {},
        "channel_id": "100",
        "user": {"id": user_id, "name": "learner"},
    }


async def test_mode_toggle_restarts_pi_with_new_prompt() -> None:
    engine, hub, pi = await _started()
    assert engine._test_mode is True  # noqa: SLF001
    result = await engine.dispatch(command("mode", {"setting": "live"}))
    assert result == {"defer": True, "ephemeral": False}
    await __import__("asyncio").sleep(0)  # let the followup task run
    assert engine._test_mode is False  # noqa: SLF001
    pi.close.assert_awaited_once()
    assert "TEST MODE IS ON" not in pi.system_prompt


async def test_mode_toggle_rejects_bad_values() -> None:
    engine, hub, pi = await _started()
    await engine.dispatch(command("mode", {"setting": "banana"}))
    pi.close.assert_not_awaited()
    assert engine._test_mode is True  # noqa: SLF001


async def test_strangers_cannot_toggle_mode() -> None:
    engine, hub, pi = await _started()
    await engine.dispatch(command("mode", {"setting": "live"}, user_id="999"))
    pi.close.assert_not_awaited()
    assert engine._test_mode is True  # noqa: SLF001


def lesson_env(tmp_path: Any) -> dict:
    return {"TEACHING_AGENT_LESSON_STATE_FILE": str(tmp_path / "state.json")}


def pi_reply(text: str) -> Any:
    return PiRunResult(
        text=text, session_id="s", session_file=None,
        provider="openrouter", model_id="m",
        input_tokens=1, output_tokens=1, cost=0.0,
    )


async def test_lesson_start_creates_thread_and_posts_milestone(tmp_path) -> None:
    engine, hub, pi = make_engine(lesson_env(tmp_path))
    hub.create_thread.return_value = {"id": "777"}
    pi.prompt.return_value = pi_reply("[lesson: start | State machines]\nLet's begin.")
    await engine.dispatch(message("Alvar, teach me state machines"))
    hub.create_thread.assert_awaited_once_with(100, "State machines")
    posted = [c.args[1] for c in hub.post_message.await_args_list]
    assert any("Lesson started: State machines" in t for t in posted)
    # The directive line is stripped; the learner only sees the reply.
    assert posted[-1] == "Let's begin."
    assert engine._lessons.thread_id == 777  # noqa: SLF001


async def test_transcripts_go_to_active_lesson_thread(tmp_path) -> None:
    engine, hub, pi = make_engine(lesson_env(tmp_path))
    hub.create_thread.return_value = {"id": "777"}
    pi.prompt.return_value = pi_reply("[lesson: start | State machines]\nBegin.")
    await engine.dispatch(message("Alvar, go"))
    hub.post_message.reset_mock()
    await engine.post_voice_transcript("why does CLOSING exist?", "crash witness")
    target = hub.post_message.await_args.args[0]
    assert target == 777
    # No active lesson → main channel.
    engine._lessons._thread_id = None  # noqa: SLF001
    await engine.post_voice_transcript("a", "b")
    assert hub.post_message.await_args.args[0] == 100


async def test_lesson_end_posts_milestone_and_clears_state(tmp_path) -> None:
    state_file = tmp_path / "state.json"
    engine, hub, pi = make_engine({"TEACHING_AGENT_LESSON_STATE_FILE": str(state_file)})
    hub.create_thread.return_value = {"id": "777"}
    pi.prompt.return_value = pi_reply("[lesson: start | State machines]\nBegin.")
    await engine.dispatch(message("Alvar, go"))
    assert state_file.exists()  # binding persisted (lessons can span days)
    pi.prompt.return_value = pi_reply("[lesson: end | known (explained)]\nWell done.")
    await engine.dispatch(message("Alvar, that's a wrap"))
    posted = [c.args[1] for c in hub.post_message.await_args_list]
    assert any("Lesson complete: State machines** — known (explained)" in t for t in posted)
    assert engine._lessons.thread_id is None  # noqa: SLF001
    assert not state_file.exists()


async def test_active_lesson_survives_restart(tmp_path) -> None:
    state_file = tmp_path / "state.json"
    state_file.write_text('{"thread_id": 777, "topic": "State machines"}')
    engine, hub, _ = make_engine({"TEACHING_AGENT_LESSON_STATE_FILE": str(state_file)})
    await engine.post_voice_transcript("a", "b")
    assert hub.post_message.await_args.args[0] == 777


async def test_mid_lesson_milestone_posts_to_main(tmp_path) -> None:
    engine, hub, pi = make_engine(lesson_env(tmp_path))
    hub.create_thread.return_value = {"id": "777"}
    pi.prompt.return_value = pi_reply("[lesson: start | Races]\nBegin.")
    await engine.dispatch(message("Alvar, go"))
    hub.post_message.reset_mock()
    pi.prompt.return_value = pi_reply(
        "[lesson: milestone | guarded write recalled unaided]\nExactly right."
    )
    await engine.dispatch(message("Alvar, is this a guarded write?"))
    posted = [c.args[1] for c in hub.post_message.await_args_list]
    assert any("📍 **Races:** guarded write recalled unaided" in t for t in posted)
    assert posted[-1] == "Exactly right."


async def test_reply_without_directives_is_untouched(tmp_path) -> None:
    engine, hub, pi = make_engine(lesson_env(tmp_path))
    pi.prompt.return_value = pi_reply("plain reply")
    await engine.dispatch(message("Alvar, hi"))
    hub.create_thread.assert_not_awaited()
    hub.post_message.assert_awaited_once_with(100, "plain reply")


async def test_test_mode_strips_write_tools() -> None:
    """The boundary is the tool surface, not the prompt: in test mode pi
    launches with read-only tools; live mode restores full tools."""
    engine, hub, pi = await _started()
    assert engine._test_mode is True  # noqa: SLF001
    assert pi.tools == ("read", "grep", "find", "ls")
    await engine.dispatch(command("mode", {"setting": "live"}))
    assert pi.tools is None
    await engine.dispatch(command("mode", {"setting": "test"}))
    assert pi.tools == ("read", "grep", "find", "ls")


async def test_every_prompt_carries_the_real_date() -> None:
    engine, hub, pi = await _started()
    await engine.dispatch(message("Alvar, hi"))
    sent = pi.prompt.await_args.args[0]
    assert sent.startswith(f"[date: {date.today().isoformat()}] ")


async def test_lesson_command_start_binds_thread(tmp_path) -> None:
    """The /lesson backstop drives the same binding pi's directives use."""
    engine, hub, pi = make_engine(lesson_env(tmp_path))
    hub.create_thread.return_value = {"id": "888"}
    result = await engine.dispatch(command("lesson", {"action": "start", "value": "Races"}))
    assert result == {"defer": True, "ephemeral": False}
    hub.create_thread.assert_awaited_once_with(100, "Races")
    assert engine._lessons.thread_id == 888  # noqa: SLF001
    # Voice transcripts now land in the thread.
    await engine.post_voice_transcript("a", "b")
    assert hub.post_message.await_args.args[0] == 888


async def test_lesson_command_end_clears_binding(tmp_path) -> None:
    engine, hub, pi = make_engine(lesson_env(tmp_path))
    hub.create_thread.return_value = {"id": "888"}
    await engine.dispatch(command("lesson", {"action": "start", "value": "Races"}))
    await engine.dispatch(command("lesson", {"action": "end", "value": "known (explained)"}))
    assert engine._lessons.thread_id is None  # noqa: SLF001
    posted = [c.args[1] for c in hub.post_message.await_args_list]
    assert any("Lesson complete: Races** — known (explained)" in t for t in posted)


async def test_lesson_command_start_requires_topic(tmp_path) -> None:
    engine, hub, pi = make_engine(lesson_env(tmp_path))
    await engine.dispatch(command("lesson", {"action": "start"}))
    hub.create_thread.assert_not_awaited()
    followup = hub.post_followup.await_args
    assert followup.kwargs.get("ephemeral") is True


async def test_lesson_command_status_reports(tmp_path) -> None:
    engine, hub, pi = make_engine(lesson_env(tmp_path))
    await engine.dispatch(command("lesson", {"action": "status"}))
    assert "No active lesson" in hub.post_followup.await_args.args[1]
