"""Tests for the session architecture (decision log 2026-10-06):
registry lifecycle, boot-scan recovery, /close rotation, lesson-owned
sessions, NEXT-BOOT consumption, and the warn-never-force cost rule."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock

from teaching_agent.config import Settings
from teaching_agent.engine import TeachingEngine
from teaching_agent.pi_rpc import PiRunResult
from teaching_agent.sessions import (
    CLOSING,
    COMPLETE,
    MAIN_OWNER,
    OPEN,
    SessionRegistry,
    lesson_owner,
)

ENV = {
    "DISCORD_CHANNEL_ID": "100",
    "DISCORD_ALLOWED_USER_ID": "42",
    "TEACHING_AGENT_NAME": "Alvar",
}


def make_engine(
    tmp_path, extra_env: dict | None = None
) -> tuple[TeachingEngine, AsyncMock, AsyncMock]:
    env = {
        **ENV,
        "TEACHING_AGENT_SESSION_REGISTRY_FILE": str(tmp_path / "registry.json"),
        "TEACHING_AGENT_LESSON_STATE_FILE": str(tmp_path / "lesson.json"),
        **(extra_env or {}),
    }
    settings = Settings.from_environment(env, env_file=None)
    hub = AsyncMock()
    pi = AsyncMock()
    pi.prompt.return_value = PiRunResult(
        text="reply", session_id="s", session_file="data/pi-sessions/s1.json",
        provider="openrouter", model_id="m",
        input_tokens=1, output_tokens=1, cost=0.10,
    )
    pi.new_session.return_value = {"sessionFile": "data/pi-sessions/s2.json"}
    return TeachingEngine(settings, hub, pi), hub, pi


def message(text: str, **extra: Any) -> dict[str, Any]:
    return {
        "channel_id": "100",
        "author": {"id": "42", "name": "learner"},
        "text": text,
        **extra,
    }


def command(name: str, options: dict | None = None) -> dict[str, Any]:
    return {
        "type": "command",
        "interaction_id": "i1",
        "command": name,
        "options": options or {},
        "channel_id": "100",
        "user": {"id": "42", "name": "learner"},
    }


# --- registry unit tests -------------------------------------------------


def test_registry_persists_lifecycle(tmp_path) -> None:
    path = tmp_path / "registry.json"
    registry = SessionRegistry(path)
    record = registry.create(session_file="s1", owner=MAIN_OWNER)
    registry.touch(record.id, session_file="s1", cost=0.25)
    registry.mark_closing(record.id)

    reloaded = SessionRegistry(path)
    revived = reloaded.get(record.id)
    assert revived is not None
    assert revived.state == CLOSING
    assert revived.turns == 1
    assert revived.cost_usd == 0.25
    reloaded.mark_complete(record.id)
    assert SessionRegistry(path).get(record.id).state == COMPLETE


def test_boot_scan_ages_out_orphans(tmp_path) -> None:
    registry = SessionRegistry(tmp_path / "registry.json")
    # OPEN session owned by a lesson that no longer exists.
    dead_lesson = registry.create(session_file="s1", owner=lesson_owner(999))
    # Ancient ownerless session.
    ancient = registry.create(session_file="s2", owner=None)
    ancient.created_at = (datetime.now(UTC) - timedelta(days=30)).isoformat()
    registry._save()  # noqa: SLF001
    # Live main session and one owned by the active lesson survive.
    main = registry.create(session_file="s3", owner=MAIN_OWNER)
    active = registry.create(session_file="s4", owner=lesson_owner(555))

    scan = registry.boot_scan(orphan_days=7, active_lesson_thread=555)
    assert registry.get(dead_lesson.id).state == COMPLETE
    assert registry.get(ancient.id).state == COMPLETE
    assert {r.id for r in scan.open} == {main.id, active.id}


def test_boot_scan_logs_one_summary_line_not_two_per_orphan(tmp_path, caplog) -> None:
    """A backlog of orphans is routine (every run that ended without /close
    leaves one); boot must not print a two-line wall per record."""
    import logging

    registry = SessionRegistry(tmp_path / "registry.json")
    for i in range(25):
        registry.create(session_file=f"s{i}", owner=lesson_owner(999 + i))

    with caplog.at_level(logging.INFO, logger="teaching_agent.sessions"):
        registry.boot_scan(orphan_days=7, active_lesson_thread=None)

    aged = [r for r in caplog.messages if "aged out" in r]
    assert len(aged) == 1
    assert "25 orphaned session(s)" in aged[0]


def test_boot_scan_returns_closing_for_recovery(tmp_path) -> None:
    registry = SessionRegistry(tmp_path / "registry.json")
    record = registry.create(session_file="s1", owner=MAIN_OWNER)
    registry.mark_closing(record.id)
    scan = registry.boot_scan(orphan_days=7, active_lesson_thread=None)
    assert [r.id for r in scan.closing] == [record.id]
    assert scan.open == []


def test_complete_sessions_are_never_returned(tmp_path) -> None:
    registry = SessionRegistry(tmp_path / "registry.json")
    record = registry.create(session_file="s1", owner=MAIN_OWNER)
    registry.mark_complete(record.id)
    scan = registry.boot_scan(orphan_days=7, active_lesson_thread=None)
    assert scan.open == [] and scan.closing == []
    assert registry.find_by_owner(MAIN_OWNER) is None


# --- engine integration --------------------------------------------------


async def test_first_turn_registers_a_main_session(tmp_path) -> None:
    engine, hub, pi = make_engine(tmp_path)
    await engine.start()
    await engine.dispatch(message("Alvar, hi"))
    registry = SessionRegistry(engine._settings.session_registry_file)  # noqa: SLF001
    records = registry.all()
    assert len(records) == 1
    assert records[0].owner == MAIN_OWNER
    assert records[0].state == OPEN
    assert records[0].session_file == "data/pi-sessions/s1.json"


async def test_close_rotates_to_a_fresh_session(tmp_path) -> None:
    engine, hub, pi = make_engine(tmp_path)
    await engine.start()
    await engine.dispatch(message("Alvar, teach me"))
    result = await engine.dispatch(command("close"))
    assert result == {"defer": True, "ephemeral": False}
    import asyncio

    await asyncio.sleep(0)
    await asyncio.sleep(0)
    pi.new_session.assert_awaited_once()
    records = engine._sessions.all()  # noqa: SLF001
    old, new = records[0], records[1]
    assert old.state == COMPLETE and old.closed_at is not None
    assert new.state == OPEN and new.session_file == "data/pi-sessions/s2.json"
    assert engine._current.id == new.id  # noqa: SLF001


async def test_boot_reattaches_open_main_session(tmp_path) -> None:
    registry = SessionRegistry(tmp_path / "registry.json")
    registry.create(session_file="data/pi-sessions/old.json", owner=MAIN_OWNER)
    engine, hub, pi = make_engine(tmp_path)
    await engine.start()
    assert pi.session_file == "data/pi-sessions/old.json"
    # The reattached session stays current: no new record on next turn.
    await engine.dispatch(message("Alvar, hi"))
    assert len(engine._sessions.all()) == 1  # noqa: SLF001


async def test_boot_finishes_interrupted_close(tmp_path) -> None:
    registry = SessionRegistry(tmp_path / "registry.json")
    record = registry.create(session_file="data/pi-sessions/hung.json", owner=MAIN_OWNER)
    registry.mark_closing(record.id)
    engine, hub, pi = make_engine(tmp_path)
    await engine.start()
    # The close checklist ran against the hung session file...
    pi.close.assert_awaited()
    prompt_text = pi.prompt.await_args.args[0]
    assert "interrupted mid-close" in prompt_text
    # ...and the record completed rather than spawning a new OPEN session.
    assert engine._sessions.get(record.id).state == COMPLETE  # noqa: SLF001
    assert len(engine._sessions.all()) == 1  # noqa: SLF001
    assert pi.session_file is None  # nothing reattached


async def test_lesson_start_claims_clean_session_without_closing(tmp_path) -> None:
    engine, hub, pi = make_engine(tmp_path)
    await engine.start()
    await engine.dispatch(message("Alvar, hi"))  # 1 turn on the main session
    hub.create_thread.return_value = {"id": "555"}
    await engine.dispatch(command("lesson", {"action": "start", "value": "Races"}))
    # Dirty session (1 turn) was auto-closed and the fresh one belongs to
    # the lesson.
    pi.new_session.assert_awaited_once()
    records = engine._sessions.all()  # noqa: SLF001
    assert records[0].state == COMPLETE
    assert records[1].owner == lesson_owner(555)


async def test_lesson_start_on_fresh_session_just_retypes(tmp_path) -> None:
    engine, hub, pi = make_engine(tmp_path)
    await engine.start()
    # Register a clean (0-turn) session directly, as a just-rotated boot would.
    engine._current = engine._sessions.create(session_file="s0", owner=MAIN_OWNER)  # noqa: SLF001
    hub.create_thread.return_value = {"id": "555"}
    await engine.dispatch(command("lesson", {"action": "start", "value": "Races"}))
    pi.new_session.assert_not_awaited()
    assert engine._current.owner == lesson_owner(555)  # noqa: SLF001


async def test_lesson_end_completes_its_session_forever(tmp_path) -> None:
    engine, hub, pi = make_engine(tmp_path)
    await engine.start()
    hub.create_thread.return_value = {"id": "555"}
    await engine.dispatch(command("lesson", {"action": "start", "value": "Races"}))
    await engine.dispatch(message("working on it", thread={"id": "555", "name": "Races"}))
    await engine.dispatch(command("lesson", {"action": "end", "value": "done"}))
    records = engine._sessions.all()  # noqa: SLF001
    lesson_session = next(r for r in records if r.owner == lesson_owner(555))
    assert lesson_session.state == COMPLETE
    # A fresh main session took over; the closed lesson's transcript is frozen.
    assert engine._current.owner == MAIN_OWNER  # noqa: SLF001
    assert engine._current.session_file != lesson_session.session_file  # noqa: SLF001


async def test_next_boot_is_consumed_exactly_once(tmp_path) -> None:
    knowledge = tmp_path / "kb"
    (knowledge / "sessions").mkdir(parents=True)
    boot = knowledge / "sessions" / "NEXT-BOOT.md"
    boot.write_text("owed: crash-window check, due today", encoding="utf-8")
    engine, hub, pi = make_engine(
        tmp_path, {"TEACHING_AGENT_KNOWLEDGE_ROOT": str(knowledge)}
    )
    await engine.start()
    assert not boot.exists()  # renamed so it can't be consumed twice
    assert list((knowledge / "sessions").glob("NEXT-BOOT.consumed-*.md"))
    await engine.dispatch(message("Alvar, hi"))
    first_prompt = pi.prompt.await_args.args[0]
    assert "boot context" in first_prompt
    assert "owed: crash-window check" in first_prompt
    await engine.dispatch(message("Alvar, again"))
    assert "boot context" not in pi.prompt.await_args.args[0]


async def test_next_boot_is_never_spent_on_a_dying_session(tmp_path) -> None:
    """Crash mid-/close leaves a CLOSING session AND a NEXT-BOOT.md. The
    recovery prompt must go to the dying session bare; the handoff note
    belongs to the surviving session."""
    registry = SessionRegistry(tmp_path / "registry.json")
    record = registry.create(session_file="data/pi-sessions/hung.json", owner=MAIN_OWNER)
    registry.mark_closing(record.id)
    knowledge = tmp_path / "kb"
    (knowledge / "sessions").mkdir(parents=True)
    (knowledge / "sessions" / "NEXT-BOOT.md").write_text(
        "owed: invariant names", encoding="utf-8"
    )
    engine, hub, pi = make_engine(
        tmp_path, {"TEACHING_AGENT_KNOWLEDGE_ROOT": str(knowledge)}
    )
    await engine.start()
    recovery_prompt = pi.prompt.await_args.args[0]
    assert "interrupted mid-close" in recovery_prompt
    assert "invariant names" not in recovery_prompt  # not spent on the dead
    # The surviving session's first turn gets the handoff note.
    await engine.dispatch(message("Alvar, hi"))
    assert "invariant names" in pi.prompt.await_args.args[0]


async def test_lesson_end_checkpoints_before_freezing(tmp_path) -> None:
    """/lesson end freezes the lesson's session COMPLETE — it must run the
    closing checklist first, or the working memory is discarded unextracted."""
    engine, hub, pi = make_engine(tmp_path)
    await engine.start()
    hub.create_thread.return_value = {"id": "555"}
    await engine.dispatch(command("lesson", {"action": "start", "value": "Races"}))
    await engine.dispatch(message("working on it", thread={"id": "555", "name": "Races"}))
    pi.prompt.reset_mock()
    await engine.dispatch(command("lesson", {"action": "end", "value": "done"}))
    close_prompts = [
        c.args[0] for c in pi.prompt.await_args_list if "closing checklist" in c.args[0]
    ]
    assert len(close_prompts) == 1
    pi.new_session.assert_awaited_once()  # rotated AFTER the checklist
    lesson_session = next(
        r for r in engine._sessions.all() if r.owner == lesson_owner(555)  # noqa: SLF001
    )
    assert lesson_session.state == COMPLETE


async def test_cost_threshold_warns_but_never_forces_rotation(tmp_path) -> None:
    engine, hub, pi = make_engine(
        tmp_path, {"TEACHING_AGENT_SESSION_COST_WARN_USD": "0.15"}
    )
    await engine.start()
    await engine.dispatch(message("Alvar, one"))   # cumulative $0.10
    await engine.dispatch(message("Alvar, two"))   # cumulative $0.20 -> warn
    warnings = [
        c for c in hub.post_message.await_args_list
        if "💸" in str(c)
    ]
    assert len(warnings) == 1
    pi.new_session.assert_not_awaited()  # warned, never force-reset
    await engine.dispatch(message("Alvar, three"))  # one warning per session
    assert len([c for c in hub.post_message.await_args_list if "💸" in str(c)]) == 1
