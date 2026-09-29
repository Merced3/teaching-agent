"""Routing between discord-hub and the Pi teacher.

Deliberately thin: every pedagogical decision (what to ask, how to grade,
when to write to the knowledge base) is delegated to Pi, whose behavior is
defined by the markdown in the knowledge root — AGENTS.md, docs/, maps/,
sessions/. This module only transports and guards.

Slash commands are prompts, not logic: /recall, /close, and /status each
translate to an instruction to Pi. Changing what they mean is a docs edit.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from .config import Settings
from .hub_client import HubClient, HubError
from .pi_rpc import PiRpcClient, PiRpcError
from .voice.runtime import VoiceError, VoiceRuntime

logger = logging.getLogger(__name__)

_SILENT = "SILENT"

_COMMANDS = [
    {"name": "recall", "description": "Run any recall checks that are due, right now."},
    {"name": "close", "description": "Close the session: update the knowledge base and commit."},
    {"name": "status", "description": "Where am I? Current state and next milestone, briefly."},
    {
        "name": "mode",
        "description": "Switch test mode: test = never write to the knowledge base.",
        "options": [
            {
                "name": "setting",
                "description": "test or live",
                "type": "string",
                "required": True,
            }
        ],
    },
    {
        "name": "voice",
        "description": "Voice session control and live provider/model swapping.",
        "options": [
            {
                "name": "action",
                "description": "start, stop, status, stt, tts, voice, model",
                "type": "string",
                "required": True,
            },
            {
                "name": "value",
                "description": "channel id, provider name, voice id, or provider/model-id",
                "type": "string",
                "required": False,
            },
        ],
    },
]

_COMMAND_PROMPTS = {
    "recall": (
        "The learner ran /recall. Check the real current date, read "
        "docs/current-state.md, and run any recall checks that are owed. If none are "
        "due, say so in one sentence and state when the next one is due."
    ),
    "close": (
        "The learner ran /close. Run the full session-closing checklist from "
        "docs/session-handoff.md: update docs/current-state.md, docs/learner.md if "
        "anything true was learned, append to docs/decision-log.md if any approach "
        "changed, record the next owed recall check, write a session log under "
        "sessions/, then commit the changes to git. Confirm briefly what you wrote."
    ),
    "status": (
        "The learner ran /status. In under 10 sentences: the loop's purpose, my "
        "current known state, and the next milestone, per docs/current-state.md and "
        "the most recent session logs. Check the real date and flag anything stale."
    ),
}

_RECALL_TICK_PROMPT = (
    "This is a scheduled recall tick, not a learner message. Check the real current "
    "date, then read docs/current-state.md and the relevant session logs. If any "
    "recall checks are due or overdue, ask the learner ONE of them now, plainly, "
    "one new word per sentence. If nothing is due, reply with exactly: SILENT"
)


def build_system_prompt(settings: Settings, *, test_mode: bool) -> str:
    """The teacher's standing orders: the handoff protocol plus channel context."""
    handoff_path = settings.knowledge_root / "docs" / "session-handoff.md"
    handoff = handoff_path.read_text(encoding="utf-8") if handoff_path.is_file() else ""
    parts = [
        f"You are {settings.agent_name}, the learner's personal teacher, operating "
        "through a Discord chat surface. Your working directory is the knowledge "
        "base itself; read and write it directly with your file tools.",
        "",
        "Standing protocol (from docs/session-handoff.md):",
        handoff.strip(),
        "",
        "Channel rules:",
        "- The learner's messages arrive prefixed with context like "
        "'[thread: name]'. Reply as a teacher in conversation: plain language "
        "first, one idea at a time, short by default.",
        "- Your final assistant text each turn is posted verbatim to Discord. "
        "Never include internal notes in it.",
        "- Git-commit knowledge-base changes at session close.",
    ]
    if test_mode:
        parts.extend(
            [
                "",
                "TEST MODE IS ON: never write to docs/, maps/, sessions/, or lessons/. "
                "Answer and teach conversationally only, and say nothing about test "
                "mode unless asked.",
            ]
        )
    return "\n".join(parts)


class TeachingEngine:
    """Owns registration, message routing, and the (opt-in) recall tick."""

    def __init__(
        self,
        settings: Settings,
        hub: HubClient,
        pi: PiRpcClient,
        voice: VoiceRuntime | None = None,
    ) -> None:
        self._settings = settings
        self._hub = hub
        self._pi = pi
        self._voice = voice
        self._test_mode = settings.test_mode
        self._last_voice_channel_id: int | None = None

    def set_voice(self, voice: VoiceRuntime) -> None:
        """Attach the voice layer post-construction: the runtime needs the
        engine's pi callback, and the engine needs the runtime — a setter
        breaks the cycle honestly."""
        self._voice = voice

    async def start(self) -> None:
        """Claim the channel and declare commands. Idempotent across restarts."""
        try:
            await self._hub.register_channel(
                self._settings.discord_channel_id,
                self._settings.callback_url,
                display_name=self._settings.agent_name,
                avatar_url=self._settings.avatar_url,
                voice_events=self._settings.voice_enabled,
            )
            logger.info("Registered channel %s.", self._settings.discord_channel_id)
        except HubError as exc:
            if exc.status_code == 409:
                logger.info("Channel already registered; keeping existing registration.")
            else:
                raise
        await self._hub.put_commands(self._settings.callback_url, _COMMANDS)
        logger.info("Slash commands synced.")

    async def dispatch(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        if payload.get("type") == "command":
            if await self._handle_command(payload):
                return {"defer": True, "ephemeral": False}
            return None
        if payload.get("type") == "voice_state":
            return await self._handle_voice_state(payload)
        return await self._handle_message(payload)

    async def _handle_message(self, payload: dict[str, Any]) -> None:
        author = payload.get("author") or {}
        if str(author.get("id")) != str(self._settings.discord_allowed_user_id):
            logger.info("Ignored message from unauthorized author %s.", author.get("id"))
            return None

        text = str(payload.get("text") or "").strip()
        if not text:
            return None

        thread = payload.get("thread") or {}
        channel_id = int(thread.get("id") or payload.get("channel_id"))
        prompt = f"[thread: {thread['name']}] {text}" if thread.get("name") else text

        reply = await self._ask_pi(channel_id, prompt)
        if reply:
            await self._hub.post_message(channel_id, reply)
        return None

    async def _handle_command(self, payload: dict[str, Any]) -> bool:
        """Kick off command handling; True means the caller should defer."""
        command = str(payload.get("command") or "")
        interaction_id = str(payload.get("interaction_id") or "")
        user = payload.get("user") or {}
        if not interaction_id:
            return False
        if str(user.get("id")) != str(self._settings.discord_allowed_user_id):
            await self._hub.post_followup(interaction_id, "Not your tutor.", ephemeral=True)
            return True
        if command == "mode":
            await self._handle_mode(payload)
            return True
        if command == "voice":
            await self._handle_voice_command(payload)
            return True
        prompt = _COMMAND_PROMPTS.get(command)
        if prompt is None:
            return False

        channel_id = int(payload.get("channel_id"))

        async def run() -> None:
            reply = await self._ask_pi(channel_id, prompt)
            await self._hub.post_followup(
                interaction_id, reply or "(nothing to say)", ephemeral=False
            )

        asyncio.create_task(run())
        return True

    async def _handle_mode(self, payload: dict[str, Any]) -> None:
        """Flip test mode live: rebuild pi's system prompt and restart the
        subprocess (the RPC client resumes the same session file, so the
        conversation survives). Operational toggle — code-owned, not a prompt."""
        interaction_id = str(payload.get("interaction_id"))
        setting = str((payload.get("options") or {}).get("setting") or "").strip().lower()
        if setting not in {"test", "live"}:
            await self._hub.post_followup(
                interaction_id, "Usage: /mode test or /mode live", ephemeral=True
            )
            return
        want_test = setting == "test"
        if want_test == self._test_mode:
            await self._hub.post_followup(
                interaction_id, f"Already in {setting} mode.", ephemeral=True
            )
            return
        self._test_mode = want_test
        self._pi.system_prompt = build_system_prompt(self._settings, test_mode=want_test)
        await self._pi.close()
        logger.info("Test mode toggled: %s", want_test)
        note = (
            "TEST MODE ON — I won't write to the knowledge base."
            if want_test
            else "LIVE MODE — session close will write to the knowledge base and commit."
        )
        await self._hub.post_followup(interaction_id, note, ephemeral=False)

    async def _handle_voice_state(self, payload: dict[str, Any]) -> None:
        """Learner joined/left/moved voice channels (registration opted in).
        Auto-join policy: follow the learner into whatever channel they enter;
        end the session when they leave voice entirely."""
        if self._voice is None:
            return None
        user = payload.get("user") or {}
        if str(user.get("id")) != str(self._settings.discord_allowed_user_id):
            return None
        after = payload.get("after_channel_id")
        if after is not None:
            self._last_voice_channel_id = int(after)
        if not self._settings.voice_autojoin:
            return None
        try:
            if after is not None:
                await self._voice.join(int(after))
            elif self._voice.is_active:
                await self._voice.leave()
        except (HubError, VoiceError) as exc:
            logger.exception("Voice auto-join handling failed.")
            await self._hub.post_message(
                self._settings.discord_channel_id, f"(voice hiccup: {exc})"
            )
        return None

    async def _handle_voice_command(self, payload: dict[str, Any]) -> None:
        interaction_id = str(payload.get("interaction_id"))
        options = payload.get("options") or {}
        action = str(options.get("action") or "").strip().lower()
        value = str(options.get("value") or "").strip()

        async def say(text: str, *, ephemeral: bool = False) -> None:
            await self._hub.post_followup(interaction_id, text, ephemeral=ephemeral)

        if self._voice is None:
            await say("Voice is disabled (TEACHING_AGENT_VOICE_ENABLED).", ephemeral=True)
            return

        try:
            if action == "start":
                channel_id = int(value) if value else self._last_voice_channel_id
                if channel_id is None:
                    await say(
                        "I don't know which voice channel you're in — join one first, "
                        "or pass the channel id: /voice action:start value:<id>",
                        ephemeral=True,
                    )
                    return
                await self._voice.join(channel_id)
                await say(f"Joined voice channel {channel_id}. Talk to me.")
            elif action == "stop":
                await self._voice.leave()
                await say("Left voice.")
            elif action == "status":
                await say(self._voice.describe(), ephemeral=True)
            elif action == "stt":
                name = await self._voice.set_stt(value)
                await say(f"Ears swapped → {name}.")
            elif action == "tts":
                name = await self._voice.set_tts(value)
                await say(f"Voice engine swapped → {name}.")
            elif action == "voice":
                voice_id = await self._voice.set_voice(value)
                await say(f"Speaking voice set to `{voice_id}` (next reply onward).")
            elif action == "model":
                await self._pi.set_model(value)
                await say(f"Teacher brain switched to `{value}`.")
            else:
                await say(
                    "Actions: start, stop, status, stt <name>, tts <name>, "
                    "voice <voice-id>, model <provider/model-id>",
                    ephemeral=True,
                )
        except (VoiceError, PiRpcError, HubError, ValueError) as exc:
            await say(f"Voice command failed: {exc}", ephemeral=True)

    async def post_voice_transcript(self, learner_text: str, reply: str) -> None:
        """Keep the text channel as the record of spoken exchanges."""
        try:
            await self._hub.post_message(
                self._settings.discord_channel_id,
                f"🎙 **You:** {learner_text}\n**{self._settings.agent_name}:** {reply}",
            )
        except HubError:
            logger.debug("Transcript post failed; continuing.", exc_info=True)

    async def recall_tick(self) -> None:
        """Scheduled job: let Pi decide whether a recall check is due."""
        if not self._settings.recall_pings_enabled:
            return
        reply = await self._ask_pi(self._settings.discord_channel_id, _RECALL_TICK_PROMPT)
        if reply and not reply.strip().upper().startswith(_SILENT):
            await self._hub.post_message(self._settings.discord_channel_id, reply)

    async def ask_pi(self, prompt: str) -> str | None:
        """Public entry for the voice layer: same pi session as text."""
        return await self._ask_pi(self._settings.discord_channel_id, prompt)

    async def _ask_pi(self, channel_id: int, prompt: str) -> str | None:
        try:
            await self._hub.typing(channel_id)
        except HubError:
            logger.debug("Typing indicator failed; continuing.", exc_info=True)
        try:
            result = await self._pi.prompt(prompt)
        except PiRpcError as exc:
            logger.exception("Pi run failed.")
            return f"(teacher brain hiccuped: {exc})"
        logger.info(
            "Pi run: model=%s/%s cost=$%.4f",
            result.provider, result.model_id, result.cost,
        )
        return result.text
