"""The full-duplex voice conversation with the learner.

Transport: discord-hub owns Discord. We ``POST /voice/join``, then attach
the duplex stream (``WS /voice/stream``): per-speaker PCM frames and
speaking events flow in, PCM frames flow out and play continuously.

Pipeline per turn: utterance (STT) → pi (same session as text; the
teacher) → streamed TTS → paced frames to the hub.

Interruption policy (ours, per the hub contract): the hub's
``speaking started`` event for the *learner* cancels the agent's current
turn immediately — pi run and TTS playback both. Because outbound audio
is paced to stay only ~300 ms ahead of playback, the learner hears the
agent stop almost at once. A generation counter discards stale work.

Providers (STT/TTS) and the pi model are swappable live via /voice.
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import websockets

from .pcm import stereo_48k_to_mono_16k
from .stt import STTProvider
from .tts import TTSProvider

logger = logging.getLogger(__name__)

_FRAME_BYTES = 3840  # 20 ms of s16le 48 kHz stereo (hub contract)
_FRAME_SECONDS = 0.020
_MAX_LEAD_SECONDS = 0.300  # stay this far ahead of playback (bounds barge-in lag)

AskPi = Callable[[str], Awaitable[str | None]]
PostTranscript = Callable[[str, str], Awaitable[None]]

_VOICE_TURN_TEMPLATE = (
    "[voice session — spoken turn] The learner said (speech-to-text): {text}\n"
    "Reply in spoken style: 1–3 short sentences, plain language, no markdown, "
    "no lists, nothing that reads badly out loud. Skip file tools unless the "
    "learner explicitly asks you to read or write something."
)


class VoiceConversation:
    """Owns one voice session: hub connection, stream, STT, and turns."""

    def __init__(
        self,
        *,
        hub: Any,
        hub_ws_url: str,
        owner: str,
        allowed_user_id: int,
        stt: STTProvider,
        tts: TTSProvider,
        ask_pi: AskPi,
        post_transcript: PostTranscript | None = None,
    ) -> None:
        self._hub = hub
        self._hub_ws_url = hub_ws_url
        self._owner = owner
        self._allowed_user_id = str(allowed_user_id)
        self._stt = stt
        self._tts = tts
        self._ask_pi = ask_pi
        self._post_transcript = post_transcript

        self._ws: websockets.ClientConnection | None = None
        self._reader_task: asyncio.Task[None] | None = None
        self._turn_task: asyncio.Task[None] | None = None
        self._generation = 0
        self.channel_id: int | None = None

    # -- provider / brain swapping (live, via /voice) ---------------------

    async def set_stt(self, stt: STTProvider) -> str:
        """Swap ears mid-session: restart the transcription feed."""
        old, self._stt = self._stt, stt
        if self.is_active:
            await old.stop()
            self._wire_stt()
            await self._stt.start()
        return type(stt).__name__

    def set_tts(self, tts: TTSProvider) -> str:
        """Swap voice; takes effect on the next spoken turn."""
        self._tts = tts
        return type(tts).__name__

    # -- lifecycle ----------------------------------------------------------

    @property
    def is_active(self) -> bool:
        return self._ws is not None

    async def join(self, channel_id: int) -> None:
        if self.is_active:
            if self.channel_id == channel_id:
                return
            await self.leave()
        await self._hub.voice_join(channel_id, self._owner)
        self.channel_id = channel_id
        self._ws = await websockets.connect(
            f"{self._hub_ws_url}/voice/stream?owner={self._owner}",
            max_size=8 * 1024 * 1024,
        )
        self._wire_stt()
        await self._stt.start()
        self._reader_task = asyncio.create_task(self._read_loop(), name="voice-reader")
        logger.info("Voice session started in channel %s.", channel_id)

    async def leave(self) -> None:
        self._interrupt()
        if self._reader_task is not None:
            self._reader_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._reader_task
            self._reader_task = None
        if self._ws is not None:
            with contextlib.suppress(Exception):
                await self._ws.close()
            self._ws = None
        with contextlib.suppress(Exception):
            await self._stt.stop()
        channel_id = self.channel_id
        self.channel_id = None
        with contextlib.suppress(Exception):
            await self._hub.voice_leave(self._owner)
        logger.info("Voice session ended (was channel %s).", channel_id)

    def _wire_stt(self) -> None:
        self._stt.on_utterance = self._on_utterance

    # -- inbound ------------------------------------------------------------

    async def _read_loop(self) -> None:
        assert self._ws is not None
        try:
            async for raw in self._ws:
                if isinstance(raw, bytes):
                    continue
                event = json.loads(raw)
                if event.get("user_id") != self._allowed_user_id:
                    continue
                if event.get("type") == "audio":
                    pcm = base64.b64decode(event["pcm"])
                    self._stt.feed(stereo_48k_to_mono_16k(pcm))
                elif event.get("type") == "speaking" and event.get("state") == "started":
                    self._interrupt()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Voice stream reader died.")
            await self.leave()

    def _interrupt(self) -> None:
        """The learner is speaking: stop any reply in flight, right now."""
        self._generation += 1
        if self._turn_task is not None and not self._turn_task.done():
            self._turn_task.cancel()
            logger.info("Turn interrupted by learner speech.")

    def _on_utterance(self, text: str) -> None:
        if not self.is_active:
            return
        self._generation += 1
        if self._turn_task is not None and not self._turn_task.done():
            self._turn_task.cancel()
        generation = self._generation
        self._turn_task = asyncio.create_task(
            self._run_turn(generation, text), name="voice-turn"
        )

    # -- one turn -----------------------------------------------------------

    async def _run_turn(self, generation: int, learner_text: str) -> None:
        logger.info("Voice turn %d — learner: %s", generation, learner_text)
        try:
            reply = await self._ask_pi(_VOICE_TURN_TEMPLATE.format(text=learner_text))
            if generation != self._generation or not reply:
                return
            await self._speak(generation, reply)
            if generation == self._generation and self._post_transcript is not None:
                await self._post_transcript(learner_text, reply)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Voice turn %d failed.", generation)

    async def _speak(self, generation: int, text: str) -> None:
        """Stream TTS into the hub, paced ~300 ms ahead of playback so an
        interruption leaves almost nothing buffered hub-side."""
        ws = self._ws
        if ws is None:
            return
        started = asyncio.get_running_loop().time()
        frames_sent = 0
        buffer = b""
        async for chunk in self._tts.stream_hub_pcm(text):
            if generation != self._generation:
                return
            buffer += chunk
            while len(buffer) >= _FRAME_BYTES:
                frame, buffer = buffer[:_FRAME_BYTES], buffer[_FRAME_BYTES:]
                await ws.send(frame)
                frames_sent += 1
                ahead = frames_sent * _FRAME_SECONDS - (
                    asyncio.get_running_loop().time() - started
                )
                if ahead > _MAX_LEAD_SECONDS:
                    await asyncio.sleep(ahead - _MAX_LEAD_SECONDS)
        # Trailing partial frame: pad with silence so nothing is dropped.
        if buffer and generation == self._generation:
            await ws.send(buffer.ljust(_FRAME_BYTES, b"\x00"))
