"""Owns the voice session and the swappable layers behind it.

The engine delegates everything voice-shaped here: joining/leaving the
hub's voice connection, and live-swapping STT (ears), TTS (voice), and
voice identity — the plumbing behind the /voice command. Swaps while a
session is running restart only the layer being swapped; swaps while
idle take effect on the next join.
"""

from __future__ import annotations

import logging
from typing import Any

from ..config import Settings
from .conversation import AskPi, TranscriptSink, VoiceConversation
from .ptt import RemotePTT
from .stt import STT_PROVIDERS, DeepgramSTT, STTProvider
from .transport import BridgeTransport, DiscordTransport, VoiceTransport
from .tts import TTS_PROVIDERS, ElevenLabsTTS, TTSProvider

logger = logging.getLogger(__name__)


class VoiceError(RuntimeError):
    """Raised for unknown providers and other voice-layer misconfiguration."""


class VoiceRuntime:
    def __init__(
        self,
        settings: Settings,
        hub: Any,
        ask_pi: AskPi,
        transcript: TranscriptSink | None = None,
        remote_ptt: RemotePTT | None = None,
    ) -> None:
        self._settings = settings
        self._ask_pi = ask_pi
        self._transcript = transcript
        self._owner = settings.callback_url
        self._transport = self._make_transport(settings, hub)
        self._stt_name = settings.voice_stt_provider
        self._tts_name = settings.voice_tts_provider
        self._voice_id = settings.voice_tts_voice_id
        self._remote_ptt = remote_ptt
        self._conversation: VoiceConversation | None = None

    @staticmethod
    def _make_transport(settings: Settings, hub: Any) -> VoiceTransport:
        if settings.voice_transport == "bridge":
            bridge_ws_url = settings.voice_bridge_url.replace(
                "http://", "ws://"
            ).replace("https://", "wss://")
            return BridgeTransport(bridge_ws_url)
        if settings.voice_transport == "discord":
            hub_ws_url = settings.hub_url.replace("http://", "ws://").replace(
                "https://", "wss://"
            )
            return DiscordTransport(hub, hub_ws_url, settings.discord_allowed_user_id)
        raise VoiceError(
            f"Unknown voice transport {settings.voice_transport!r}. "
            "Available: discord, bridge"
        )

    # -- introspection ------------------------------------------------------

    @property
    def is_active(self) -> bool:
        return self._conversation is not None and self._conversation.is_active

    @property
    def channel_id(self) -> int | None:
        return self._conversation.channel_id if self._conversation else None

    @property
    def requires_channel(self) -> bool:
        """Discord sessions start in a channel; the bridge is channel-less."""
        return self._transport.requires_channel

    def describe(self) -> str:
        state = (
            f"active in channel {self.channel_id}"
            if self.is_active
            else "idle (join a voice channel, or /voice action:start)"
        )
        return (
            f"Voice {state}\n"
            f"Transport: {self._settings.voice_transport}\n"
            f"STT (ears): {self._stt_name} — available: {', '.join(STT_PROVIDERS)}\n"
            f"TTS (voice): {self._tts_name} — available: {', '.join(TTS_PROVIDERS)}\n"
            f"TTS voice id: {self._voice_id or '(unset)'}"
        )

    # -- session ------------------------------------------------------------

    async def join(self, channel_id: int | None = None) -> None:
        if self._conversation is None:
            self._conversation = VoiceConversation(
                transport=self._transport,
                owner=self._owner,
                stt=self._make_stt(),
                tts=self._make_tts(),
                ask_pi=self._ask_pi,
                transcript=self._transcript,
                filler_dir=self._settings.voice_filler_dir,
                remote_ptt=self._remote_ptt,
            )
        await self._conversation.join(channel_id)

    async def leave(self) -> None:
        if self._conversation is not None:
            await self._conversation.leave()

    # -- live swaps -----------------------------------------------------------

    async def set_stt(self, name: str) -> str:
        self._require(name, STT_PROVIDERS, "STT")
        self._stt_name = name
        if self.is_active:
            assert self._conversation is not None
            await self._conversation.set_stt(self._make_stt())
        return name

    async def set_tts(self, name: str) -> str:
        self._require(name, TTS_PROVIDERS, "TTS")
        self._tts_name = name
        if self.is_active:
            assert self._conversation is not None
            self._conversation.set_tts(self._make_tts())
        return name

    async def set_voice(self, voice_id: str) -> str:
        """Change the speaking voice (e.g. a Jarvis id) — next spoken turn."""
        self._voice_id = voice_id
        if self.is_active:
            assert self._conversation is not None
            self._conversation.set_tts(self._make_tts())
        return voice_id

    # -- provider construction ------------------------------------------------

    def _make_stt(self) -> STTProvider:
        self._require(self._stt_name, STT_PROVIDERS, "STT")
        if self._stt_name == "deepgram":
            if not self._settings.deepgram_api_key:
                raise VoiceError("DEEPGRAM_API_KEY is not set.")
            return DeepgramSTT(self._settings.deepgram_api_key)
        raise VoiceError(f"No constructor for STT provider {self._stt_name!r}")

    def _make_tts(self) -> TTSProvider:
        self._require(self._tts_name, TTS_PROVIDERS, "TTS")
        if self._tts_name == "elevenlabs":
            if not self._settings.elevenlabs_api_key:
                raise VoiceError("ELEVENLABS_API_KEY is not set.")
            if not self._voice_id:
                raise VoiceError("No TTS voice id set (TEACHING_AGENT_VOICE_TTS_VOICE_ID).")
            return ElevenLabsTTS(
                self._settings.elevenlabs_api_key,
                voice_id=self._voice_id,
                model_id=self._settings.voice_tts_model_id,
            )
        raise VoiceError(f"No constructor for TTS provider {self._tts_name!r}")

    @staticmethod
    def _require(name: str, registry: dict[str, Any], kind: str) -> None:
        if name not in registry:
            raise VoiceError(
                f"Unknown {kind} provider {name!r}. Available: {', '.join(registry)}"
            )
