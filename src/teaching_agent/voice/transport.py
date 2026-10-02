"""Swappable voice transports: how the agent reaches the learner's ears.

A transport owns everything that differs between "voice over Discord" and
"voice over the phone page": how a session is acquired (join/leave), where
the duplex PCM stream lives, and whose audio events belong to the learner.
Both transports expose the same stream contract (per-speaker PCM events
in, binary PCM out), so the conversation above them is unchanged.

- ``DiscordTransport`` wraps discord-hub: ``POST /voice/join`` acquires a
  Discord voice channel, and the stream carries many speakers' audio plus
  VAD-guessed speaking events.
- ``BridgeTransport`` wraps voice-bridge: there is no channel to acquire
  (the room is the phone page's presence), the one speaker is ``"page"``,
  and speaking events are the exact button press/release edges.

Picking one is configuration, not code: ``TEACHING_AGENT_VOICE_TRANSPORT``.
"""

from __future__ import annotations

from typing import Any, Protocol


class VoiceTransport(Protocol):
    """The seam between the voice conversation and a voice carrier."""

    #: ``user_id`` value on inbound events that belong to the learner.
    speaker_id: str
    #: True when a voice channel id is needed to start a session.
    requires_channel: bool

    def stream_url(self, owner: str) -> str:
        """The duplex PCM stream to attach (``WS .../voice/stream``)."""
        ...

    async def join(self, channel_id: int | None, owner: str) -> None: ...
    async def leave(self, owner: str) -> None: ...


class DiscordTransport:
    """Voice over discord-hub: join a Discord voice channel, then stream."""

    requires_channel = True

    def __init__(self, hub: Any, hub_ws_url: str, allowed_user_id: int) -> None:
        self._hub = hub
        self._hub_ws_url = hub_ws_url
        self.speaker_id = str(allowed_user_id)

    def stream_url(self, owner: str) -> str:
        return f"{self._hub_ws_url}/voice/stream?owner={owner}"

    async def join(self, channel_id: int | None, owner: str) -> None:
        assert channel_id is not None, "Discord voice requires a channel id."
        await self._hub.voice_join(channel_id, owner)

    async def leave(self, owner: str) -> None:
        await self._hub.voice_leave(owner)


class BridgeTransport:
    """Voice over voice-bridge: the phone page IS the room, so there is
    nothing to join — attaching the stream is the whole session setup.
    Speaking events arrive as exact press/release edges, so no remote-PTT
    side channel is needed on this transport."""

    requires_channel = False
    speaker_id = "page"

    def __init__(self, bridge_ws_url: str) -> None:
        self._bridge_ws_url = bridge_ws_url

    def stream_url(self, owner: str) -> str:
        return f"{self._bridge_ws_url}/voice/stream?owner={owner}"

    async def join(self, channel_id: int | None, owner: str) -> None:
        return None  # no channel to acquire; the page's presence is the room

    async def leave(self, owner: str) -> None:
        return None
