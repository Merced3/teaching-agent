"""Simulate the voice-bridge phone page for a local end-to-end voice test.

Plays the page's role exactly: connect the duplex audio socket, press the
button, stream real speech (TTS-generated) as 48k mono s16le, release, then
record whatever the agent speaks back. Run with the teaching-agent venv:

    ./.venv/Scripts/python scripts/simulate_page.py
"""

from __future__ import annotations

import asyncio
import io
import json
import os
import wave
from pathlib import Path

import httpx
import numpy as np
import websockets
from dotenv import load_dotenv

load_dotenv("../voice-bridge/.env")
BRIDGE_TOKEN = os.environ["VOICE_BRIDGE_TOKEN"]
load_dotenv(".env", override=False)
EL_KEY = os.environ["ELEVENLABS_API_KEY"]
EL_VOICE = os.environ["TEACHING_AGENT_VOICE_TTS_VOICE_ID"]

BRIDGE = "http://localhost:8200"
BRIDGE_WS = "ws://localhost:8200"
TEXT = "Hey teacher, can you remind me what recursion is in one sentence?"


async def make_speech_48k_mono() -> bytes:
    """ElevenLabs pcm_24000 -> s16le 48kHz mono (the page's wire format)."""
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{EL_VOICE}",
            params={"output_format": "pcm_24000"},
            headers={"xi-api-key": EL_KEY, "Content-Type": "application/json"},
            json={"text": TEXT, "model_id": "eleven_turbo_v2_5"},
        )
        r.raise_for_status()
    pcm = np.frombuffer(r.content, dtype=np.int16)
    upsampled = np.repeat(pcm, 2)  # 24k -> 48k
    return upsampled.astype(np.int16).tobytes()


async def main() -> None:
    speech = await make_speech_48k_mono()
    print(f"speech clip: {len(speech) / 96000:.1f}s of 48k mono")

    received = bytearray()
    async with websockets.connect(
        f"{BRIDGE_WS}/voice/page/audio?token={BRIDGE_TOKEN}", max_size=8 * 1024 * 1024
    ) as ws:

        async def listen() -> None:
            async for msg in ws:
                if isinstance(msg, bytes):
                    received.extend(msg)

        listener = asyncio.create_task(listen())

        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BRIDGE}/voice/ptt", json={"state": "down", "token": BRIDGE_TOKEN}
            )
            print("press:", r.status_code)

        # stream the clip in real-time 20ms frames (960 samples * 2 bytes)
        frame = 960 * 2
        for i in range(0, len(speech), frame):
            await ws.send(speech[i : i + frame])
            await asyncio.sleep(0.02)

        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BRIDGE}/voice/ptt", json={"state": "up", "token": BRIDGE_TOKEN}
            )
            print("release:", r.status_code)

        # wait for the reply (pi + TTS can take a while)
        for _ in range(60):
            await asyncio.sleep(1)
            if len(received) > 96000 * 2:  # >2s of reply audio
                break
        listener.cancel()

    print(f"received {len(received)} bytes back ({len(received) / 96000:.1f}s)")
    if received:
        pcm = np.frombuffer(bytes(received), dtype=np.int16)
        print(f"reply peak amplitude: {np.abs(pcm).max()} (0 = silence)")
        out = Path("out/simulated-page-reply.pcm")
        out.parent.mkdir(exist_ok=True)
        out.write_bytes(bytes(received))
        print(f"saved -> {out} (s16le 48kHz mono)")


if __name__ == "__main__":
    asyncio.run(main())
