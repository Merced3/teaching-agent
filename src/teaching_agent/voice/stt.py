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

    def __init__(self, api_key: str, *, model: str = "nova-3") -> None:
        super().__init__()
        self._api_key = api_key
        self._url = self._URL.replace("model=nova-3", f"model={model}")
        self._ws: websockets.ClientConnection | None = None
        self._reader: asyncio.Task[None] | None = None

    async def start(self) -> None:
        try:
            self._ws = await websockets.connect(
                self._url,
                additional_headers={"Authorization": f"Token {self._api_key}"},
                max_size=8 * 1024 * 1024,
            )
        except Exception as exc:
            raise STTError(f"Deepgram connection failed: {exc}") from exc
        self._reader = asyncio.create_task(self._read_loop(), name="deepgram-reader")
        logger.info("Deepgram STT session started.")

    def feed(self, pcm_mono_16k: bytes) -> None:
        ws = self._ws
        if ws is None:
            return
        with contextlib.suppress(RuntimeError):
            asyncio.get_running_loop().create_task(ws.send(pcm_mono_16k))

    async def stop(self) -> None:
        if self._reader is not None:
            self._reader.cancel()
            self._reader = None
        if self._ws is not None:
            try:
                await self._ws.send(json.dumps({"type": "CloseStream"}))
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

    async def _read_loop(self) -> None:
        assert self._ws is not None
        current: list[str] = []
        try:
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
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Deepgram reader died.")
        finally:
            remainder = " ".join(current).strip()
            if remainder:
                self.on_utterance(remainder)


STT_PROVIDERS: dict[str, Callable[..., STTProvider]] = {
    "deepgram": DeepgramSTT,
}
