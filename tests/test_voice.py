"""Black-box tests for the voice boundary: PCM wire conversions, who the
agent follows into voice, and what the /voice command guards. Turn
mechanics (barge-in, pacing) need a live hub — verified by ear, not here."""

from __future__ import annotations

from unittest.mock import AsyncMock

import numpy as np

from teaching_agent.config import Settings
from teaching_agent.engine import TeachingEngine
from teaching_agent.voice.pcm import mono_24k_to_stereo_48k, stereo_48k_to_mono_16k

ENV = {
    "DISCORD_CHANNEL_ID": "100",
    "DISCORD_ALLOWED_USER_ID": "42",
    "TEACHING_AGENT_VOICE_ENABLED": "true",
    "DEEPGRAM_API_KEY": "x",
    "ELEVENLABS_API_KEY": "y",
    "TEACHING_AGENT_VOICE_TTS_VOICE_ID": "z",
}


def make_engine() -> tuple[TeachingEngine, AsyncMock, AsyncMock, AsyncMock]:
    settings = Settings.from_environment(ENV, env_file=None)
    hub, pi, voice = AsyncMock(), AsyncMock(), AsyncMock()
    return TeachingEngine(settings, hub, pi, voice=voice), hub, pi, voice


# -- PCM wire conversions ---------------------------------------------------


def test_hub_frame_downmixes_and_decimates() -> None:
    # One second of constant signal, s16le 48 kHz stereo.
    samples = np.full(48000 * 2, 1000, dtype=np.int16)
    out = stereo_48k_to_mono_16k(samples.tobytes())
    result = np.frombuffer(out, dtype=np.int16)
    assert result.size == 16000
    assert np.all(np.abs(result - 1000) <= 1)


def test_tts_chunk_upsamples_to_hub_format() -> None:
    samples = np.arange(2400, dtype=np.int16)  # 100 ms of 24 kHz mono
    out = mono_24k_to_stereo_48k(samples.tobytes())
    result = np.frombuffer(out, dtype=np.int16)
    assert result.size == 2400 * 4  # 2x upsample, 2 channels
    assert result[0] == result[1] == result[2] == result[3] == 0
    assert result[4] == 1  # each source sample repeated 4x


# -- voice_state routing ------------------------------------------------------


async def test_follows_the_learner_into_voice() -> None:
    engine, hub, _, voice = make_engine()
    await engine.dispatch(
        {"type": "voice_state", "user": {"id": "42"}, "after_channel_id": "555"}
    )
    voice.join.assert_awaited_once_with(555)


async def test_ignores_other_users_voice_events() -> None:
    engine, hub, _, voice = make_engine()
    await engine.dispatch(
        {"type": "voice_state", "user": {"id": "999"}, "after_channel_id": "555"}
    )
    voice.join.assert_not_awaited()


async def test_leaves_when_the_learner_leaves() -> None:
    engine, hub, _, voice = make_engine()
    voice.is_active = True
    await engine.dispatch(
        {"type": "voice_state", "user": {"id": "42"}, "after_channel_id": None}
    )
    voice.leave.assert_awaited_once()


# -- /voice command guards ----------------------------------------------------


async def test_voice_model_failure_is_reported_not_raised() -> None:
    from teaching_agent.pi_rpc import PiRpcError

    engine, hub, pi, _ = make_engine()
    pi.set_model.side_effect = PiRpcError("Model must be 'provider/model-id'")
    result = await engine.dispatch(
        {
            "type": "command",
            "command": "voice",
            "interaction_id": "i1",
            "user": {"id": "42"},
            "channel_id": "100",
            "options": {"action": "model", "value": "not-a-model"},
        }
    )
    assert result == {"defer": True, "ephemeral": False}
    hub.post_followup.assert_awaited_once()
    args = hub.post_followup.call_args
    assert "Voice command failed" in args.args[1]


# -- turn-taking: PTT finalize + thinking fillers ----------------------------

import asyncio
import json
from types import SimpleNamespace

from teaching_agent.voice import conversation as conv
from teaching_agent.voice.conversation import VoiceConversation


class FakeSTT:
    def __init__(self) -> None:
        self.on_utterance = lambda _t: None
        self.finalized = 0
        self.fed = b""

    async def start(self) -> None: ...
    def feed(self, pcm: bytes) -> None:
        self.fed += pcm
    def finalize(self) -> None:
        self.finalized += 1
    async def stop(self) -> None: ...


class FakeWS:
    """Scripted inbound stream; records outbound frames."""

    def __init__(self, messages: list[dict]) -> None:
        self._messages = messages
        self.sent: list[bytes] = []

    def __aiter__(self):
        async def gen():
            for m in self._messages:
                yield json.dumps(m)
        return gen()

    async def send(self, data) -> None:
        if isinstance(data, bytes):
            self.sent.append(data)

    async def close(self) -> None: ...


def make_conversation(ws_messages, *, ask_pi=None, filler_dir=None):
    stt = FakeSTT()
    transport = SimpleNamespace(
        speaker_id="42",
        stream_url=lambda owner: "ws://unused/voice/stream",
        join=AsyncMock(),
        leave=AsyncMock(),
    )
    conversation = VoiceConversation(
        transport=transport,
        owner="test",
        stt=stt,
        tts=AsyncMock(),
        ask_pi=ask_pi or (AsyncMock(return_value="reply")),
        filler_dir=filler_dir,
    )
    ws = FakeWS(ws_messages)
    conversation._ws = ws
    return conversation, stt, ws


async def test_ptt_release_finalizes_stt_turn() -> None:
    conversation, stt, _ = make_conversation(
        [
            {"type": "speaking", "user_id": "42", "state": "started"},
            {"type": "speaking", "user_id": "42", "state": "stopped"},
        ]
    )
    await conversation._read_loop()
    assert stt.finalized == 1


async def test_other_users_speaking_stop_does_not_finalize() -> None:
    conversation, stt, _ = make_conversation(
        [{"type": "speaking", "user_id": "999", "state": "stopped"}]
    )
    await conversation._read_loop()
    assert stt.finalized == 0


async def test_filler_plays_during_slow_pi(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(conv, "_FILLER_DELAY_SECONDS", 0.05)
    monkeypatch.setattr(conv, "_FILLER_INTERVAL_SECONDS", 0.05)
    clip = b"\x01\x00" * (48000 * 2 // 10)  # 100 ms of hub-format PCM
    (tmp_path / "filler-1.pcm").write_bytes(clip)

    async def slow_pi(_text: str) -> str:
        await asyncio.sleep(0.2)
        return "reply"

    conversation, _, ws = make_conversation([], ask_pi=slow_pi, filler_dir=tmp_path)
    reply = await conversation._ask_with_fillers(conversation._generation, "hello")
    assert reply == "reply"
    assert ws.sent  # at least one filler frame went out before pi answered


async def test_no_filler_when_pi_is_fast(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(conv, "_FILLER_DELAY_SECONDS", 0.2)
    (tmp_path / "filler-1.pcm").write_bytes(b"\x01\x00" * 9600)

    async def fast_pi(_text: str) -> str:
        return "reply"

    conversation, _, ws = make_conversation([], ask_pi=fast_pi, filler_dir=tmp_path)
    reply = await conversation._ask_with_fillers(conversation._generation, "hello")
    assert reply == "reply"
    assert not ws.sent


async def test_missing_filler_dir_is_silent_noop(tmp_path) -> None:
    conversation, _, ws = make_conversation(
        [], filler_dir=tmp_path / "does-not-exist"
    )
    reply = await conversation._ask_with_fillers(conversation._generation, "hello")
    assert reply == "reply"
    assert not ws.sent


async def test_utterances_merge_and_fire_only_after_speaking_stops(monkeypatch) -> None:
    """The PTT hold is the floor: mid-hold endpointing fragments must not
    fire turns; release + grace fires one merged turn."""
    monkeypatch.setattr(conv, "_FLUSH_GRACE_SECONDS", 0.02)
    fired: list[str] = []

    async def ask_pi(text: str) -> str:
        fired.append(text)
        return "reply"

    conversation, stt, _ = make_conversation(
        [
            {"type": "speaking", "user_id": "42", "state": "started"},
            {"type": "speaking", "user_id": "42", "state": "stopped"},
        ],
        ask_pi=ask_pi,
    )
    # Learner holds the key; Deepgram endpoints mid-hold (the bug).
    conversation._learner_speaking = True
    conversation._on_utterance("Why is the sky")
    await asyncio.sleep(0.05)
    assert fired == []  # nothing fired while holding
    # Release: speaking stopped -> finalize + grace -> merged turn.
    conversation._learner_speaking = False
    conversation._on_utterance("blue?")
    conversation._schedule_flush()
    await asyncio.sleep(0.1)
    assert len(fired) == 1
    assert "Why is the sky blue?" in fired[0]


async def test_speaking_again_during_grace_cancels_flush(monkeypatch) -> None:
    """VAD flap / re-press inside the grace window must not fire the turn."""
    monkeypatch.setattr(conv, "_FLUSH_GRACE_SECONDS", 0.05)
    fired: list[str] = []

    async def ask_pi(text: str) -> str:
        fired.append(text)
        return "reply"

    conversation, _, _ = make_conversation([], ask_pi=ask_pi)
    conversation._on_utterance("wait I")
    conversation._schedule_flush()
    await asyncio.sleep(0.02)  # inside the grace window
    conversation._learner_speaking = True
    conversation._cancel_flush()  # what speaking-started does
    conversation._on_utterance("meant to ask more")
    await asyncio.sleep(0.1)
    assert fired == []
    assert conversation._pending_utterances == ["wait I", "meant to ask more"]


# -- remote PTT: dual-mode turn boundary --------------------------------------

from teaching_agent.voice.ptt import RemotePTT


def test_remote_ptt_mode_follows_heartbeat_freshness() -> None:
    ptt = RemotePTT(heartbeat_timeout_seconds=0.05)
    assert not ptt.connected
    ptt.heartbeat()
    assert ptt.connected
    import time
    time.sleep(0.08)
    assert not ptt.connected  # lapsed heartbeat -> back to AUTO


def test_remote_ptt_press_release_events() -> None:
    ptt = RemotePTT()
    events: list[str] = []
    ptt.on_press = lambda: events.append("press")
    ptt.on_release = lambda: events.append("release")
    ptt.press()
    ptt.press()  # held: no double-fire
    ptt.release()
    ptt.release()  # not held: no spurious release
    assert events == ["press", "release"]


async def test_manual_mode_press_holds_release_fires(monkeypatch) -> None:
    monkeypatch.setattr(conv, "_FLUSH_GRACE_SECONDS", 0.02)
    fired: list[str] = []

    async def ask_pi(text: str) -> str:
        fired.append(text)
        return "reply"

    ptt = RemotePTT()
    conversation, stt, _ = make_conversation([], ask_pi=ask_pi)
    conversation._remote_ptt = ptt
    ptt.on_press = conversation._remote_press
    ptt.on_release = conversation._remote_release

    ptt.heartbeat()  # button in hand -> MANUAL mode
    ptt.press()
    conversation._on_utterance("Why is the sky")
    await asyncio.sleep(0.05)
    assert fired == []  # held floor: fragment accumulated, nothing fired
    ptt.release()
    await asyncio.sleep(0.1)
    assert len(fired) == 1 and "Why is the sky" in fired[0]
    assert stt.finalized == 1


async def test_hub_speaking_events_ignored_in_manual_mode() -> None:
    ptt = RemotePTT()
    ptt.heartbeat()
    conversation, stt, _ = make_conversation(
        [{"type": "speaking", "user_id": "42", "state": "stopped"}]
    )
    conversation._remote_ptt = ptt
    await conversation._read_loop()
    assert stt.finalized == 0  # audio-VAD noise did not act as a boundary


async def test_ptt_routes_and_auth() -> None:
    from httpx import ASGITransport, AsyncClient

    from teaching_agent.callback_server import create_callback_app

    ptt = RemotePTT()
    app = create_callback_app(AsyncMock(return_value=None), remote_ptt=ptt, ptt_token="s3cret")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        bad = await client.post("/voice/ptt", json={"state": "down", "token": "wrong"})
        assert bad.status_code == 403 and not ptt.pressed
        down = await client.post("/voice/ptt", json={"state": "down", "token": "s3cret"})
        assert down.status_code == 204 and ptt.pressed
        up = await client.post("/voice/ptt", json={"state": "up", "token": "s3cret"})
        assert up.status_code == 204 and not ptt.pressed
        hb = await client.post("/voice/ptt/heartbeat", json={"token": "s3cret"})
        assert hb.status_code == 204 and ptt.connected
        page = await client.get("/ptt")
        assert page.status_code == 200 and "Hold to talk" in page.text


# -- transports ---------------------------------------------------------------

from teaching_agent.voice.transport import BridgeTransport, DiscordTransport


async def test_discord_transport_joins_hub_and_targets_learner() -> None:
    hub = AsyncMock()
    transport = DiscordTransport(hub, "ws://hub:8100", allowed_user_id=42)
    assert transport.requires_channel
    assert transport.speaker_id == "42"
    assert transport.stream_url("me") == "ws://hub:8100/voice/stream?owner=me"
    await transport.join(7, "me")
    hub.voice_join.assert_awaited_once_with(7, "me")
    await transport.leave("me")
    hub.voice_leave.assert_awaited_once_with("me")


async def test_bridge_transport_is_channel_less_and_speaks_page_events() -> None:
    transport = BridgeTransport("ws://bridge:8200")
    assert not transport.requires_channel
    assert transport.speaker_id == "page"
    assert transport.stream_url("me") == "ws://bridge:8200/voice/stream?owner=me"
    # join/leave are no-ops: there is no channel to acquire on the bridge.
    assert await transport.join(None, "me") is None
    assert await transport.leave("me") is None


async def test_bridge_press_release_edges_drive_turns() -> None:
    """On the bridge, speaking events ARE the button: release finalizes the
    turn with no remote-PTT side channel attached."""
    conversation, stt, _ = make_conversation(
        [
            {"type": "speaking", "user_id": "page", "state": "started"},
            {"type": "speaking", "user_id": "page", "state": "stopped"},
        ]
    )
    conversation._transport.speaker_id = "page"
    assert conversation._remote_ptt is None
    await conversation._read_loop()
    assert stt.finalized == 1


async def test_stt_empty_speech_final_still_flushes_utterance() -> None:
    """Deepgram sends the final transcript with is_final, then a SEPARATE
    speech_final message whose transcript is empty (the Finalize response).
    The empty message must still flush the accumulated utterance — this was
    the 2026-10 dead-air bug: turns never fired."""
    import json as _json

    from teaching_agent.voice.stt import DeepgramSTT

    messages = [
        {"type": "Results", "is_final": True, "speech_final": False,
         "channel": {"alternatives": [{"transcript": "what is recursion"}]}},
        {"type": "Results", "is_final": True, "speech_final": True,
         "channel": {"alternatives": [{"transcript": ""}]}},
    ]

    class FakeDGSocket:
        def __aiter__(self):
            async def gen():
                for m in messages:
                    yield _json.dumps(m)
            return gen()

    stt = DeepgramSTT("key")
    stt._ws = FakeDGSocket()
    heard: list[str] = []
    stt.on_utterance = heard.append
    remainder = await stt._consume([])
    assert heard == ["what is recursion"]
    assert remainder == []


async def test_stt_finalize_pending_fires_on_next_final_without_speech_final() -> None:
    """Deepgram's Finalize response is unreliable about speech_final; after
    a finalize() the next is_final with accumulated text IS the utterance."""
    import json as _json

    from teaching_agent.voice.stt import DeepgramSTT

    messages = [
        {"type": "Results", "is_final": True, "speech_final": False,
         "channel": {"alternatives": [{"transcript": "what is recursion"}]}},
        # ...and then silence forever: no speech_final ever arrives.
    ]

    class FakeDGSocket:
        def __aiter__(self):
            async def gen():
                for m in messages:
                    yield _json.dumps(m)
            return gen()

    stt = DeepgramSTT("key")
    stt._ws = FakeDGSocket()
    stt._finalize_pending = True  # as finalize() sets
    heard: list[str] = []
    stt.on_utterance = heard.append
    await stt._consume([])
    assert heard == ["what is recursion"]
