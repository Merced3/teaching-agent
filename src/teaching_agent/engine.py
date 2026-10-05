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
import re
from contextlib import suppress
from datetime import date
from typing import Any

from .config import Settings
from .hub_client import HubClient, HubError
from .lectures import (
    LectureError,
    render_lecture_audio,
    resolve_lesson_file,
    split_directive,
)
from .lessons import LessonManager
from .pi_rpc import PiRpcClient, PiRpcError
from .voice.conversation import TranscriptSink
from .voice.runtime import VoiceError, VoiceRuntime

logger = logging.getLogger(__name__)

_SILENT = "SILENT"

_COMMANDS = [
    {"name": "recall", "description": "Run any recall checks that are due, right now."},
    {"name": "close", "description": "Close the session: update the knowledge base and commit."},
    {
        "name": "next",
        "description": "What should I focus on? Owed recall checks + the recommended next lesson.",
    },
    {
        # Named /progress, not /status: command names are unique across ALL
        # projects on the hub, and socratic-partner owns "status" (2026-09-30
        # collision, first live multi-client evidence for integrations §6).
        "name": "progress",
        "description": "Where am I? Current state and next milestone, briefly.",
    },
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
        # Code-owned backstop for pi's [lesson: ...] directives: the model's
        # boundary detection is probabilistic; this is the deterministic
        # override. Same LessonManager, same thread/milestone effects.
        "name": "lesson",
        "description": "Lesson thread control: start/end the active lesson manually.",
        "options": [
            {
                "name": "action",
                "description": "start, end, or status",
                "type": "string",
                "required": True,
            },
            {
                "name": "value",
                "description": "topic (for start) or summary (for end)",
                "type": "string",
                "required": False,
            },
        ],
    },
    {
        # Code-owned like /mode and /lesson: generating audio is a build
        # action, and pi's tools deliberately exclude building. Pi writes
        # the markdown (knowledge-base authoring), the code renders and
        # serves it, and the link goes to the channel.
        "name": "lecture",
        "description": "Generate a podcast-lecture audio episode on a topic (link posted here).",
        "options": [
            {
                "name": "topic",
                "description": "what the episode should teach (paste from /next if you like)",
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
    "next": (
        "The learner ran /next. Check the real date (the [date:] prefix), then read "
        "docs/current-state.md, the maps in maps/, and recent session logs. Give a "
        "short prioritized list: first any recall checks that are due or overdue "
        "(say how overdue), then the ONE next lesson you recommend and a sentence "
        "why. Under 12 sentences. This is a menu, not a lecture."
    ),
    "progress": (
        "The learner ran /progress. In under 10 sentences: the loop's purpose, my "
        "current known state, and the next milestone, per docs/current-state.md and "
        "the most recent session logs. Check the real date and flag anything stale."
    ),
}

_RECALL_TICK_PROMPT = (
    "This is a scheduled check-in, not a learner message. The [date:] prefix is the "
    "real current date — compute elapsed time from it. Read docs/current-state.md "
    "and the relevant session logs. If any recall checks are due or overdue, ask the "
    "learner ONE of them now, plainly, one new word per sentence, and close with one "
    "sentence on what comes next after it. If nothing is due, reply with exactly: SILENT"
)

_LECTURE_WRITE_PROMPT = (
    "The learner ran /lecture topic:{topic}. Write a spoken-word podcast "
    "lecture on that topic as audio-friendly markdown (no code blocks, no "
    "tables, no visual-only markup — it will be read aloud by TTS). Ground "
    "it in what the maps in maps/ and docs/current-state.md say about what "
    "the learner knows and where the edge is; teach to the edge, don't "
    "re-present what is already known. Aim for dense, not long. Save it as "
    "lessons/<slug>/lecture.md (one folder per topic, slug = short "
    "kebab-case name). Then reply in chat with 2-3 sentences about what the "
    "episode covers, and end your reply with a directive line exactly like: "
    "[lecture-file: lessons/<slug>/lecture.md]"
)

_LECTURE_RECORD_PROMPT = (
    "A lecture episode was just generated: source {source} (~{words} words, "
    "about {minutes:.0f} minutes), audio {audio}. Record it in "
    "docs/current-state.md as an episode generated on {today} and UNPROBED, "
    "with one line on what it covers, so a later /recall can probe its "
    "content (listening = presented; nothing more). Reply with exactly: SILENT"
)

# Test mode is a real boundary: pi runs with read-only tools, so the
# knowledge base cannot be written no matter what the model decides.
# (bash is excluded precisely because it can write.) The prompt text below
# documents the intent; this allowlist enforces it.
_TEST_MODE_TOOLS = ("read", "grep", "find", "ls")


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
        "- Every message you receive starts with a [date: YYYY-MM-DD] prefix. "
        "That is the real current date, computed fresh per message — trust it "
        "over any date written in the docs, and use it whenever you record "
        "dates or compute elapsed time.",
        "- The learner's messages arrive prefixed with context like "
        "'[thread: name]'. Reply as a teacher in conversation: plain language "
        "first, one idea at a time, short by default.",
        "- Your final assistant text each turn is posted verbatim to Discord. "
        "Never include internal notes in it.",
        "- Git-commit knowledge-base changes at session close.",
        "- You teach, you do not build: your write/edit tools only reach the "
        "knowledge base (docs/, maps/, sessions/, lessons/) and your shell is "
        "read-only plus git. This is enforced at the tool level — attempts to "
        "change code or config fail by design. Describe desired code changes "
        "in chat instead.",
        "- Lesson threads are how the channel stays clean: the main channel "
        "is an index of evidence, transcripts and working-out are exhaust "
        "that belongs in a thread. You control this with directive lines "
        "placed anywhere in your reply; they are stripped before your reply "
        "is posted or spoken, so the learner never sees them, and they cost "
        "you nothing to include. The directives:",
        "  [lesson: start | <topic>] — REQUIRED in the same reply where a "
        "lesson topic is settled (the learner asks for a lesson, or you "
        "agree together what to work on). Opens a thread named after the "
        "topic; voice transcripts and the working record go there.",
        "  [lesson: milestone | <what was learned, with evidence level>] — "
        "post sparingly, only for a genuine evidence event mid-lesson.",
        "  [lesson: end | <summary with evidence level>] — REQUIRED when a "
        "lesson wraps up or the learner calls it done.",
        "A recall-check chat without a lesson topic is not a lesson; no "
        "directive needed. When in doubt between starting or not, start — "
        "a stray closed thread is cheaper than a flooded main channel.",
        "- A second directive type exists for /lecture: when a prompt tells "
        "you a lecture episode was requested, you write the markdown and "
        "end your reply with [lecture-file: <path you wrote>]. The code "
        "renders that file to audio and serves the link; the line is "
        "stripped like the lesson directives.",
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
        self._pi.tools = _TEST_MODE_TOOLS if self._test_mode else None
        self._lessons = LessonManager(
            hub, settings.discord_channel_id, settings.lesson_state_file
        )
        # Audio render is injectable so tests never shell out to TTS.
        self._render_audio = render_lecture_audio

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
        if (
            self._settings.text_require_address
            and not thread.get("name")  # a thread IS the conversation; no gate
            and not re.search(
                rf"\b{re.escape(self._settings.agent_name)}\b", text, re.IGNORECASE
            )
        ):
            # The channel doubles as the learner's notepad (and voice
            # transcripts post here); only messages that address the agent
            # by name are conversation. ("Alvar" is a display name, not a
            # mentionable Discord account, so we match the word.)
            logger.info("Ignored unaddressed message: %.60s", text)
            return None

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
        if command == "lesson":
            await self._handle_lesson(payload)
            return True
        if command == "lecture":
            await self._handle_lecture(payload)
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
        self._pi.tools = _TEST_MODE_TOOLS if want_test else None
        await self._pi.close()
        logger.info("Test mode toggled: %s", want_test)
        note = (
            "TEST MODE ON — knowledge-base writes are off (I have no write tools)."
            if want_test
            else "LIVE MODE — session close will write to the knowledge base and commit."
        )
        await self._hub.post_followup(interaction_id, note, ephemeral=False)

    async def _handle_lesson(self, payload: dict[str, Any]) -> None:
        """Deterministic lesson-thread control — same code-owned category as
        /mode: boundaries the learner can force when the model doesn't fire."""
        interaction_id = str(payload.get("interaction_id"))
        options = payload.get("options") or {}
        action = str(options.get("action") or "").strip().lower()
        value = str(options.get("value") or "").strip()

        try:
            if action == "start":
                if not value:
                    await self._hub.post_followup(
                        interaction_id,
                        "Usage: /lesson action:start value:<topic>",
                        ephemeral=True,
                    )
                    return
                note = await self._lessons.start(value)
            elif action == "end":
                note = await self._lessons.end(value)
            elif action == "status":
                note = self._lessons.describe()
            else:
                await self._hub.post_followup(
                    interaction_id,
                    "Actions: start <topic>, end [summary], status",
                    ephemeral=True,
                )
                return
        except HubError as exc:
            await self._hub.post_followup(
                interaction_id, f"Lesson command failed: {exc}", ephemeral=True
            )
            return
        await self._hub.post_followup(interaction_id, note, ephemeral=False)

    async def _handle_lecture(self, payload: dict[str, Any]) -> None:
        """Podcast-lecture generation — code-owned like /mode: pi authors
        the markdown (knowledge-base work), this code renders it to audio
        and serves the link (build work pi's tools can't do)."""
        interaction_id = str(payload.get("interaction_id"))
        topic = str((payload.get("options") or {}).get("topic") or "").strip()
        if not topic:
            await self._hub.post_followup(
                interaction_id, "Usage: /lecture topic:<text>", ephemeral=True
            )
            return
        channel_id = int(payload.get("channel_id"))

        async def run() -> None:
            try:
                await self._produce_lecture(channel_id, interaction_id, topic)
            except Exception:
                logger.exception("Lecture generation failed.")
                with suppress(HubError):
                    await self._hub.post_followup(
                        interaction_id,
                        "(lecture generation failed — check the agent log)",
                        ephemeral=True,
                    )

        asyncio.create_task(run())

    async def _produce_lecture(
        self, channel_id: int, interaction_id: str, topic: str
    ) -> None:
        raw = await self._ask_pi_raw(
            channel_id, _LECTURE_WRITE_PROMPT.format(topic=topic)
        )
        if raw is None:
            await self._hub.post_followup(
                interaction_id, "(teacher brain hiccuped)", ephemeral=False
            )
            return
        declared, display = split_directive(raw)
        # Lesson directives in the reply are still honored (a lecture can
        # open a thread); the learner only sees the stripped text.
        display = await self._lessons.process(display)
        if declared is None:
            await self._hub.post_followup(
                interaction_id,
                (display + "\n\n" if display else "")
                + "⚠️ I wrote no [lecture-file:] directive, so nothing was "
                "rendered. Ask me to try again.",
                ephemeral=False,
            )
            return
        try:
            source = resolve_lesson_file(self._settings.knowledge_root, declared)
        except LectureError as exc:
            await self._hub.post_followup(
                interaction_id, f"⚠️ Lecture file problem: {exc}", ephemeral=False
            )
            return
        audio_path = source.with_name("lecture.mp3")
        try:
            await self._render_audio(
                source,
                audio_path,
                tool=self._settings.lecture_tts,
                knowledge_root=self._settings.knowledge_root,
            )
        except (LectureError, OSError) as exc:
            await self._hub.post_followup(
                interaction_id, f"⚠️ Audio render failed: {exc}", ephemeral=False
            )
            return
        relative = audio_path.resolve().relative_to(
            (self._settings.knowledge_root / "lessons").resolve()
        )
        link = f"{self._settings.lecture_public_url}/lectures/{relative.as_posix()}"
        words = len(source.read_text(encoding='utf-8').split())
        text = (
            (display + "\n\n") if display else ""
        ) + f"🎧 **Episode ready:** {link}"
        await self._hub.post_followup(interaction_id, text, ephemeral=False)
        # Retention hook: the agent generated the intake, so it records
        # what the learner consumed — a later /recall can probe it. This
        # write is pi's (knowledge base), not the code's.
        record = _LECTURE_RECORD_PROMPT.format(
            source=declared.as_posix(),
            words=words,
            minutes=words / 145,
            audio=relative.as_posix(),
            today=date.today().isoformat(),
        )
        await self._ask_pi_raw(channel_id, record)

    async def _handle_voice_state(self, payload: dict[str, Any]) -> None:
        """Learner joined/left/moved voice channels (registration opted in).
        Auto-join policy: follow the learner into whatever channel they enter;
        end the session when they leave voice entirely. Only meaningful on the
        discord transport — the bridge has no Discord voice channels."""
        if self._voice is None or not self._voice.requires_channel:
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
                if not self._voice.requires_channel:
                    # Bridge transport: the phone page is the room; no channel.
                    await self._voice.join()
                    await say("Voice session started on the bridge. Open the page and hold the button.")
                    return
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

    async def post_voice_learner(self, learner_text: str) -> None:
        """The learner's words, posted the moment a turn fires — the record
        exists even if the turn is interrupted before any answer."""
        await self._post_transcript_line(f"🎙 **You:** {learner_text}")

    async def post_voice_reply(self, reply: str, heard_seconds: float | None) -> None:
        """The agent's reply after it is spoken. A barge-in adds where the
        learner cut it off, so the log shows what was never heard."""
        text = f"🎙 **{self._settings.agent_name}:** {reply}"
        if heard_seconds is not None:
            text += (
                f"\n*(✂️ cut off — you interrupted ~{heard_seconds:.0f}s in; "
                "the text above is the full reply)*"
            )
        await self._post_transcript_line(text)

    async def post_voice_unanswered(self, learner_text: str) -> None:
        """The learner interrupted before the agent answered — the log must
        not pretend that turn was processed."""
        await self._post_transcript_line(
            "*(⚠️ interrupted — not answered; shelved into your next message)*"
        )

    def transcript_sink(self) -> TranscriptSink:
        """The voice layer's auditable-log callbacks, bound to this engine."""
        return TranscriptSink(
            learner=self.post_voice_learner,
            reply=self.post_voice_reply,
            unanswered=self.post_voice_unanswered,
        )

    async def _post_transcript_line(self, text: str) -> None:
        """Transcripts go to the active lesson thread when one is open,
        otherwise the main channel."""
        try:
            await self._hub.post_message(
                self._lessons.thread_id or self._settings.discord_channel_id,
                text,
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
        raw = await self._ask_pi_raw(channel_id, prompt)
        if raw is None:
            return None
        # Lesson directives are honored everywhere pi speaks (chat, commands,
        # voice); the learner never sees the marker lines.
        return await self._lessons.process(raw)

    async def _ask_pi_raw(self, channel_id: int, prompt: str) -> str | None:
        """Prompt pi with the date prefix; return the UNstripped reply.

        Callers that parse their own directives (e.g. /lecture) need the
        raw text; everyone else should use _ask_pi.
        """
        try:
            await self._hub.typing(channel_id)
        except HubError:
            logger.debug("Typing indicator failed; continuing.", exc_info=True)
        try:
            result = await self._pi.prompt(f"[date: {date.today().isoformat()}] {prompt}")
        except PiRpcError as exc:
            logger.exception("Pi run failed.")
            return f"(teacher brain hiccuped: {exc})"
        logger.info(
            "Pi run: model=%s/%s cost=$%.4f",
            result.provider, result.model_id, result.cost,
        )
        return result.text
