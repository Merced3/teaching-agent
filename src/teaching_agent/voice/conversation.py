"""The full-duplex voice conversation with the learner.

Transport: swappable via ``VoiceTransport`` (discord-hub or voice-bridge;
see ``transport.py``). We join (a no-op on the bridge), then attach the
duplex stream (``WS /voice/stream``): per-speaker PCM frames and speaking
events flow in, PCM frames flow out and play continuously.

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
from dataclasses import dataclass
from pathlib import Path

import websockets

from .pcm import stereo_48k_to_mono_16k
from .ptt import RemotePTT
from .stt import STTProvider
from .transport import VoiceTransport
from .tts import TTSProvider

logger = logging.getLogger(__name__)

_FRAME_BYTES = 3840  # 20 ms of s16le 48 kHz stereo (hub contract)
_FRAME_SECONDS = 0.020
_MAX_LEAD_SECONDS = 0.300  # stay this far ahead of playback (bounds barge-in lag)

AskPi = Callable[[str], Awaitable[str | None]]

# The transcript is an auditable log of what actually happened, not a
# merged summary: the learner's words post the moment a turn fires (so a
# turn that gets interrupted still appears), the reply posts after it is
# spoken (with a cut-off marker if the learner barged in), and a turn the
# learner interrupted before the agent answered gets an explicit
# "unanswered" note. Three small messages, no character-limit squeeze.
OnLearner = Callable[[str], Awaitable[None]]
OnReply = Callable[[str, float | None], Awaitable[None]]  # seconds heard; None = full
OnUnanswered = Callable[[str], Awaitable[None]]


@dataclass(frozen=True)
class TranscriptSink:
    learner: OnLearner
    reply: OnReply
    unanswered: OnUnanswered

_FILLER_DELAY_SECONDS = 2.0  # pi silence this long -> first filler
_FILLER_INTERVAL_SECONDS = 2.0  # then repeat at this interval until pi answers
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
        transport: VoiceTransport,
        owner: str,
        stt: STTProvider,
        tts: TTSProvider,
        ask_pi: AskPi,
        transcript: TranscriptSink | None = None,
        filler_dir: Path | None = None,
        filler_text: str | None = None,
        filler_interval: float = _FILLER_INTERVAL_SECONDS,
        remote_ptt: RemotePTT | None = None,
    ) -> None:
        self._transport = transport
        self._owner = owner
        self._stt = stt
        self._tts = tts
        self._ask_pi = ask_pi
        self._transcript = transcript
        self._filler_dir = filler_dir
        self._filler_clips: list[bytes] | None = None  # lazy: loaded on first use
        # Filler phrase mode (default): one fixed sentence ("Loading an answer."),
        # synthesized once per TTS voice with the ACTIVE provider (free with
        # edge), then replayed verbatim at a fixed interval. The learner asked
        # for no human-sounding variety while waiting — one signal, one meaning.
        self._filler_text = filler_text
        self._filler_interval = filler_interval
        self._filler_pcm: bytes | None = None  # lazy: synthesized on first use
        self._remote_ptt = remote_ptt

        self._ws: websockets.ClientConnection | None = None
        self._reader_task: asyncio.Task[None] | None = None
        self._turn_task: asyncio.Task[None] | None = None
        self._flush_task: asyncio.Task[None] | None = None
        self._learner_speaking = False
        self._pending_utterances: list[str] = []
        # Interrupted turns the agent never answered, kept as context for the
        # next turn: the learner's words are never silently dropped from what
        # pi sees, even when the turn that carried them died.
        self._shelved: list[str] = []
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
        """Swap voice; takes effect on the next spoken turn. The cached
        filler phrase must be re-synthesized — it should sound like the
        voice that is about to answer."""
        self._tts = tts
        self._filler_pcm = None
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

    async def join(self, channel_id: int | None = None) -> None:
        if self.is_active:
            if self.channel_id == channel_id:
                return
            await self.leave()
        await self._transport.join(channel_id, self._owner)
        self.channel_id = channel_id
        if self._remote_ptt is not None:
            self._remote_ptt.on_press = self._remote_press
            self._remote_ptt.on_release = self._remote_release
        self._ws = await websockets.connect(
            self._transport.stream_url(self._owner),
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
            await self._transport.leave(self._owner)
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
                if event.get("user_id") != self._transport.speaker_id:
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
        sink = self._transcript
        if sink is not None:
            await sink.learner(learner_text)
        # Package any shelved (previously unanswered) messages ahead of this
        # one — order preserved, depth unbounded; the transcript has already
        # logged each part separately, this is only about what pi SEES.
        prompt_text = learner_text
        if self._shelved:
            parts = "; ".join(f"({i}) {s}" for i, s in enumerate(self._shelved, 1))
            prompt_text = (
                f"[earlier message(s) the learner sent but you never answered, "
                f"oldest first: {parts}] [current message: {learner_text}]"
            )
        try:
            try:
                reply = await self._ask_with_fillers(generation, prompt_text)
            except asyncio.CancelledError:
                self._shelved.append(learner_text)
                if sink is not None:
                    await sink.unanswered(learner_text)
                raise
            if generation != self._generation or not reply:
                self._shelved.append(learner_text)
                if sink is not None:
                    await sink.unanswered(learner_text)
                return
            self._shelved.clear()  # answered: the shelf is discharged
            heard_box = [0.0]  # seconds of reply audio actually played
            try:
                await self._speak(generation, reply, heard_box)
            except asyncio.CancelledError:
                if sink is not None:
                    await sink.reply(reply, heard_box[0])
                raise
            heard = None if generation == self._generation else heard_box[0]
            if sink is not None:
                await sink.reply(reply, heard)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Voice turn %d failed.", generation)

    async def _next_filler(self, index: int) -> bytes | None:
        """The filler audio for this beat. Phrase mode returns the same
        cached clip every time; clips-dir mode rotates pre-generated files."""
        if self._filler_text:
            if self._filler_pcm is None:
                parts: list[bytes] = []
                try:
                    async for chunk in self._tts.stream_hub_pcm(self._filler_text):
                        parts.append(chunk)
                except Exception:
                    logger.exception("Filler synthesis failed; fillers off.")
                    self._filler_pcm = b""
                    return None
                self._filler_pcm = b"".join(parts)
            return self._filler_pcm or None
        clips = self._load_fillers()
        if not clips:
            return None
        return clips[index % len(clips)]

    async def _ask_with_fillers(self, generation: int, learner_text: str) -> str | None:
        """Ask pi; while it thinks in silence, say what is happening
        ("Loading an answer.") at a fixed interval — a status signal, not
        a personality. No variants by design."""
        ask = asyncio.ensure_future(
            self._ask_pi(_VOICE_TURN_TEMPLATE.format(text=learner_text))
        )
        first_delay = (
            self._filler_interval if self._filler_text else _FILLER_DELAY_SECONDS
        )
        delay = first_delay
        index = 0
        try:
            while not ask.done():
                try:
                    await asyncio.wait_for(asyncio.shield(ask), timeout=delay)
                except asyncio.TimeoutError:
                    if generation != self._generation:
                        break
                    clip = await self._next_filler(index)
                    if clip is None:
                        return await ask
                    index += 1
                    logger.info("pi still thinking — playing filler %d.", index)
                    await self._play_filler(generation, clip)
                    delay = (
                        self._filler_interval
                        if self._filler_text
                        else _FILLER_INTERVAL_SECONDS
                    )
            return await ask
        except asyncio.CancelledError:
            ask.cancel()
            raise

    async def _play_filler(self, generation: int, pcm: bytes) -> None:
        async def chunks() -> AsyncIterator[bytes]:
            yield pcm

        await self._stream_pcm(generation, chunks())

    async def _speak(self, generation: int, text: str, heard_box: list[float]) -> None:
        """Speak a reply, continuously updating heard_box[0] with roughly how
        many seconds the learner has actually heard (audio sent, minus the
        pacing lead) — so a barge-in can be logged with its cut-off point."""
        sent = 0

        async def counted() -> AsyncIterator[bytes]:
            nonlocal sent
            async for chunk in self._tts.stream_hub_pcm(text):
                sent += len(chunk)
                seconds = sent / (_FRAME_BYTES / _FRAME_SECONDS) - _MAX_LEAD_SECONDS
                heard_box[0] = max(0.0, seconds)
                yield chunk

        await self._stream_pcm(generation, counted())

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
