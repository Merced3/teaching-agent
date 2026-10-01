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
from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path
from typing import Any

import websockets

from .pcm import stereo_48k_to_mono_16k
from .ptt import RemotePTT
from .stt import STTProvider
from .tts import TTSProvider

logger = logging.getLogger(__name__)

_FRAME_BYTES = 3840  # 20 ms of s16le 48 kHz stereo (hub contract)
_FRAME_SECONDS = 0.020
_MAX_LEAD_SECONDS = 0.300  # stay this far ahead of playback (bounds barge-in lag)

AskPi = Callable[[str], Awaitable[str | None]]
PostTranscript = Callable[[str, str], Awaitable[None]]

_FILLER_DELAY_SECONDS = 2.0  # pi silence this long -> first "Mm."
_FILLER_INTERVAL_SECONDS = 3.0  # then repeat (rotating clips) until pi answers
_FLUSH_GRACE_SECONDS = 0.8  # after speaking stops, wait this long for the
# final transcript fragment before firing the merged turn

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
        filler_dir: Path | None = None,
        remote_ptt: RemotePTT | None = None,
    ) -> None:
        self._hub = hub
        self._hub_ws_url = hub_ws_url
        self._owner = owner
        self._allowed_user_id = str(allowed_user_id)
        self._stt = stt
        self._tts = tts
        self._ask_pi = ask_pi
        self._post_transcript = post_transcript
        self._filler_dir = filler_dir
        self._filler_clips: list[bytes] | None = None  # lazy: loaded on first use
        self._remote_ptt = remote_ptt

        self._ws: websockets.ClientConnection | None = None
        self._reader_task: asyncio.Task[None] | None = None
        self._turn_task: asyncio.Task[None] | None = None
        self._flush_task: asyncio.Task[None] | None = None
        self._learner_speaking = False
        self._pending_utterances: list[str] = []
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

    def _manual_mode(self) -> bool:
        """A fresh remote heartbeat means the button is in hand: turn
        boundaries come from press/release exactly, and hub speaking
        events (audio-VAD guesses) stop being boundary signals."""
        return self._remote_ptt is not None and self._remote_ptt.connected

    def _remote_press(self) -> None:
        logger.info("Remote PTT pressed — holding the floor.")
        self._learner_speaking = True
        self._cancel_flush()
        self._interrupt()

    def _remote_release(self) -> None:
        logger.info("Remote PTT released — turn over.")
        self._learner_speaking = False
        self._stt.finalize()
        self._schedule_flush()

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
        if self._remote_ptt is not None:
            self._remote_ptt.on_press = self._remote_press
            self._remote_ptt.on_release = self._remote_release
        if self._remote_ptt is not None:
            self._remote_ptt.on_press = self._remote_press
            self._remote_ptt.on_release = self._remote_release
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
        self._cancel_flush()
        self._pending_utterances.clear()
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
                elif event.get("type") == "speaking":
                    logger.info("learner speaking %s", event.get("state"))
                    if self._manual_mode():
                        # Button present: audio-VAD events are noise for
                        # boundary purposes; press/release owns the floor.
                        continue
                    if event.get("state") == "started":
                        self._learner_speaking = True
                        self._cancel_flush()  # still talking; hold the turn
                        self._interrupt()
                    elif event.get("state") == "stopped":
                        # The speaking key/mic release IS the turn boundary.
                        # Flush the STT so the last fragment lands, then
                        # fire the merged turn after a short grace.
                        self._learner_speaking = False
                        self._stt.finalize()
                        self._schedule_flush()
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
        """STT drew a fragment boundary. Never fire a turn straight from
        this — while the learner holds the floor (PTT key down / VAD
        active), fragments just accumulate. The turn belongs to the
        speaking-stopped signal, not to a silence timer."""
        if not self.is_active:
            return
        logger.info(
            "STT fragment (learner_speaking=%s): %s", self._learner_speaking, text
        )
        self._pending_utterances.append(text)
        if not self._learner_speaking:
            self._schedule_flush()

    def _cancel_flush(self) -> None:
        if self._flush_task is not None and not self._flush_task.done():
            self._flush_task.cancel()
        self._flush_task = None

    def _schedule_flush(self) -> None:
        self._cancel_flush()
        if self.is_active:
            self._flush_task = asyncio.create_task(
                self._flush_after_grace(), name="voice-flush"
            )

    async def _flush_after_grace(self) -> None:
        try:
            await asyncio.sleep(_FLUSH_GRACE_SECONDS)
        except asyncio.CancelledError:
            raise
        if self._learner_speaking or not self._pending_utterances:
            return
        text = " ".join(self._pending_utterances).strip()
        self._pending_utterances.clear()
        if not text:
            return
        logger.info("Flushing merged turn: %s", text)
        self._generation += 1
        if self._turn_task is not None and not self._turn_task.done():
            self._turn_task.cancel()
        generation = self._generation
        self._turn_task = asyncio.create_task(
            self._run_turn(generation, text), name="voice-turn"
        )

    # -- one turn -----------------------------------------------------------

    def _load_fillers(self) -> list[bytes]:
        """Pre-generated hub-format (s16le 48 kHz stereo) "thinking" clips.
        Missing directory = fillers silently off; they are a courtesy
        signal, never a requirement."""
        if self._filler_clips is None:
            clips: list[bytes] = []
            if self._filler_dir is not None and self._filler_dir.is_dir():
                for path in sorted(self._filler_dir.glob("*.pcm")):
                    with contextlib.suppress(OSError):
                        clips.append(path.read_bytes())
            self._filler_clips = clips
            logger.info(
                "Filler clips loaded: %d (dir: %s).", len(clips), self._filler_dir
            )
        return self._filler_clips

    async def _run_turn(self, generation: int, learner_text: str) -> None:
        logger.info("Voice turn %d — learner: %s", generation, learner_text)
        try:
            reply = await self._ask_with_fillers(generation, learner_text)
            if generation != self._generation or not reply:
                return
            await self._speak(generation, reply)
            if generation == self._generation and self._post_transcript is not None:
                await self._post_transcript(learner_text, reply)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Voice turn %d failed.", generation)

    async def _ask_with_fillers(self, generation: int, learner_text: str) -> str | None:
        """Ask pi; while it thinks in silence, hold the floor with a short
        pre-generated "Mm." so the learner knows to wait — a courtesy
        signal, not a second LLM job."""
        ask = asyncio.ensure_future(
            self._ask_pi(_VOICE_TURN_TEMPLATE.format(text=learner_text))
        )
        clips = self._load_fillers()
        if not clips:
            return await ask
        index = 0
        try:
            while not ask.done():
                delay = _FILLER_DELAY_SECONDS if index == 0 else _FILLER_INTERVAL_SECONDS
                try:
                    await asyncio.wait_for(asyncio.shield(ask), timeout=delay)
                except asyncio.TimeoutError:
                    if generation != self._generation:
                        break
                    logger.info("pi still thinking — playing filler %d.", index + 1)
                    await self._play_filler(generation, clips[index % len(clips)])
                    index += 1
            return await ask
        except asyncio.CancelledError:
            ask.cancel()
            raise

    async def _play_filler(self, generation: int, pcm: bytes) -> None:
        async def chunks() -> AsyncIterator[bytes]:
            yield pcm

        await self._stream_pcm(generation, chunks())

    async def _speak(self, generation: int, text: str) -> None:
        await self._stream_pcm(generation, self._tts.stream_hub_pcm(text))

    async def _stream_pcm(self, generation: int, chunks: AsyncIterator[bytes]) -> None:
        """Stream hub-format PCM into the hub, paced ~300 ms ahead of
        playback so an interruption leaves almost nothing buffered
        hub-side."""
        ws = self._ws
        if ws is None:
            return
        started = asyncio.get_running_loop().time()
        frames_sent = 0
        buffer = b""
        async for chunk in chunks:
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
