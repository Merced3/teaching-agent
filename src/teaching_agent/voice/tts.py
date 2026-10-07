"""Text-to-speech providers (the voice). Swappable seam.

A provider turns one reply string into a stream of PCM chunks in the
hub's wire format (s16le 48 kHz stereo — the conversion lives here so
the conversation layer never cares which provider is speaking). Chunked
streaming keeps time-to-first-sound low and keeps the hub's playback
buffer small, which is what makes interruption (barge-in) feel instant.

The voice *identity* (which ElevenLabs voice, which model) is
configuration, changeable live via /voice — a Jarvis sound is a
voice-id swap, not a code change.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Callable

import edge_tts
import httpx
import miniaudio

from .pcm import mono_24k_to_stereo_48k

logger = logging.getLogger(__name__)


class TTSError(RuntimeError):
    """Raised when a TTS provider cannot synthesize speech."""


class TTSProvider:
    """One text-to-speech engine binding."""

    async def stream_hub_pcm(self, text: str) -> AsyncIterator[bytes]:
        raise NotImplementedError
        yield b""  # pragma: no cover - marks this an async generator


class ElevenLabsTTS(TTSProvider):
    """ElevenLabs streaming TTS, raw PCM output (no mp3 decode step).

    ``output_format=pcm_24000`` streams s16le 24 kHz mono over plain HTTP
    chunked responses — exactly what the conversation layer can upsample
    and forward as it arrives.
    """

    _BASE = "https://api.elevenlabs.io/v1/text-to-speech"

    def __init__(
        self,
        api_key: str,
        *,
        voice_id: str,
        model_id: str = "eleven_turbo_v2_5",
    ) -> None:
        self._api_key = api_key
        self.voice_id = voice_id
        self.model_id = model_id

    async def stream_hub_pcm(self, text: str) -> AsyncIterator[bytes]:
        url = f"{self._BASE}/{self.voice_id}/stream?output_format=pcm_24000"
        headers = {"xi-api-key": self._api_key, "Content-Type": "application/json"}
        body = {"text": text, "model_id": self.model_id}
        try:
            async with (
                httpx.AsyncClient(timeout=60) as client,
                client.stream("POST", url, headers=headers, json=body) as response,
            ):
                if response.status_code >= 400:
                    detail = await response.aread()
                    raise TTSError(f"ElevenLabs failed ({response.status_code}): {detail[:200]!r}")
                pending = b""
                async for chunk in response.aiter_bytes(8192):
                    pending += chunk
                    # s16le samples are 2 bytes; never split a sample.
                    whole = pending[: len(pending) // 2 * 2]
                    pending = pending[len(whole) :]
                    if whole:
                        yield mono_24k_to_stereo_48k(whole)
                if pending:
                    yield mono_24k_to_stereo_48k(pending + b"\x00")
        except TTSError:
            raise
        except httpx.HTTPError as exc:
            raise TTSError(f"ElevenLabs unreachable: {exc}") from exc


class EdgeTTS(TTSProvider):
    """Microsoft Edge neural voices via edge-tts — free, no API key.

    Still a cloud service (Microsoft's), but costs nothing and sounds far
    more human than the fully-local options we have on Windows. edge-tts
    7.x only streams mp3 (24 kHz mono, no raw-PCM output format exists),
    so each utterance is buffered, decoded to s16le 24 kHz mono via
    miniaudio, and handed to the conversation layer in the same shape the
    ElevenLabs provider produces. Voice identity is a voice NAME (e.g.
    en-US-AndrewNeural), swappable live via /voice.
    """

    def __init__(self, *, voice_id: str, rate: str = "+0%") -> None:
        self.voice_id = voice_id
        self.rate = rate

    async def stream_hub_pcm(self, text: str) -> AsyncIterator[bytes]:
        communicate = edge_tts.Communicate(text, voice=self.voice_id, rate=self.rate)
        mp3 = bytearray()
        try:
            async for message in communicate.stream():
                if message.get("type") == "audio":
                    mp3 += message["data"]
        except Exception as exc:
            raise TTSError(f"edge-tts failed: {exc}") from exc
        if not mp3:
            raise TTSError("edge-tts returned no audio")
        try:
            decoded = miniaudio.decode(
                bytes(mp3), miniaudio.SampleFormat.SIGNED16, 1, 24000
            )
        except Exception as exc:
            raise TTSError(f"edge-tts mp3 decode failed: {exc}") from exc
        pcm = decoded.samples.tobytes()
        # Yield in ~85 ms slices (8192 bytes of s16le 24 kHz mono) so
        # barge-in bookkeeping stays granular. Never split a 2-byte sample.
        for offset in range(0, len(pcm), 8192):
            chunk = pcm[offset : offset + 8192]
            if len(chunk) % 2:
                chunk += b"\x00"
            yield mono_24k_to_stereo_48k(chunk)


TTS_PROVIDERS: dict[str, Callable[..., TTSProvider]] = {
    "elevenlabs": ElevenLabsTTS,
    "edge": EdgeTTS,
}
