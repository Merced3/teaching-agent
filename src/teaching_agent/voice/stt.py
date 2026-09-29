"""Speech-to-text providers (the ears). Swappable seam.

A provider receives a continuous feed of s16le 16 kHz mono PCM and calls
back with finished utterances. The conversation layer decides what an
utterance *means*; the provider only draws the boundary.

Adding a provider: subclass STTProvider, register it in ``STT_PROVIDERS``
at the bottom. Nothing else in the codebase should name a provider.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from collections.abc import Callable

import websockets

logger = logging.getLogger(__name__)

OnUtterance = Callable[[str], None]


class STTError(RuntimeError):
    """Raised when an STT provider cannot start or sustain a session."""


class STTProvider:
    """One streaming transcription session."""

    def __init__(self) -> None:
        self.on_utterance: OnUtterance = lambda _text: None

    async def start(self) -> None:
        raise NotImplementedError

    def feed(self, pcm_mono_16k: bytes) -> None:
        raise NotImplementedError

    async def stop(self) -> None:
        raise NotImplementedError


class DeepgramSTT(STTProvider):
    """Deepgram live transcription over websocket.

    Endpointing (``speech_final`` after a pause) is what turns the audio
    stream into utterances — that's the piece a file-drop API can't give
    a conversation. VAD events are ignored; interruption policy uses the
    hub's speaking events instead.
    """

    _URL = (
        "wss://api.deepgram.com/v1/listen"
        "?model=nova-3&encoding=linear16&sample_rate=16000&channels=1"
        "&interim_results=true&endpointing=300&smart_format=true&vad_events=true"
    )

    _KEEPALIVE_SECONDS = 8.0  # Deepgram 1011s the socket after ~10 s without data

    def __init__(self, api_key: str, *, model: str = "nova-3") -> None:
        super().__init__()
        self._api_key = api_key
        self._url = self._URL.replace("model=nova-3", f"model={model}")
        self._ws: websockets.ClientConnection | None = None
        self._reader: asyncio.Task[None] | None = None
        self._keepalive: asyncio.Task[None] | None = None
        self._stopped = False

    async def start(self) -> None:
        self._stopped = False
        await self._connect()
        self._reader = asyncio.create_task(self._read_loop(), name="deepgram-reader")
        self._keepalive = asyncio.create_task(self._keepalive_loop(), name="deepgram-keepalive")

    async def _connect(self) -> None:
        try:
            self._ws = await websockets.connect(
                self._url,
                additional_headers={"Authorization": f"Token {self._api_key}"},
                max_size=8 * 1024 * 1024,
            )
        except Exception as exc:
            raise STTError(f"Deepgram connection failed: {exc}") from exc
        logger.info("Deepgram STT session connected.")

    async def _keepalive_loop(self) -> None:
        """Voice sessions are quiet by nature; keep the socket alive through
        stretches where nobody is speaking."""
        try:
            while True:
                await asyncio.sleep(self._KEEPALIVE_SECONDS)
                ws = self._ws
                if ws is not None:
                    with contextlib.suppress(Exception):
                        await ws.send(json.dumps({"type": "KeepAlive"}))
        except asyncio.CancelledError:
            raise

    def feed(self, pcm_mono_16k: bytes) -> None:
        ws = self._ws
        if ws is None:
            return
        with contextlib.suppress(RuntimeError):
            asyncio.get_running_loop().create_task(ws.send(pcm_mono_16k))

    async def stop(self) -> None:
        self._stopped = True
        for task in (self._reader, self._keepalive):
            if task is not None:
                task.cancel()
        self._reader = None
        self._keepalive = None
        if self._ws is not None:
            try:
                await self._ws.send(json.dumps({"type": "CloseStream"}))
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

    async def _read_loop(self) -> None:
        current: list[str] = []
        while not self._stopped:
            try:
                if self._ws is None:
                    await self._connect()
                current = await self._consume(current)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Deepgram connection lost; reconnecting.")
                self._ws = None
                if not self._stopped:
                    await asyncio.sleep(1.0)
        remainder = " ".join(current).strip()
        if remainder:
            self.on_utterance(remainder)

    async def _consume(self, current: list[str]) -> list[str]:
        assert self._ws is not None
        async for raw in self._ws:
            message = json.loads(raw)
            if message.get("type") != "Results":
                continue
            channel = message.get("channel") or {}
            alternatives = channel.get("alternatives") or []
            transcript = str(alternatives[0].get("transcript", "")) if alternatives else ""
            if not transcript:
                continue
            if message.get("is_final"):
                current.append(transcript)
            if message.get("speech_final"):
                utterance = " ".join(current).strip()
                current = []
                if utterance:
                    self.on_utterance(utterance)
        return current


STT_PROVIDERS: dict[str, Callable[..., STTProvider]] = {
    "deepgram": DeepgramSTT,
}
