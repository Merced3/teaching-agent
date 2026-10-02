"""Probe: does the bridge forward page mic audio to the consumer stream?

Attaches as the consumer, plays the page, presses, sends a loud tone,
and counts audio events received. Usage: probe_bridge.py [tone|speech]
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import sys

import httpx
import numpy as np
import websockets
from dotenv import load_dotenv

load_dotenv("../voice-bridge/.env")
TOKEN = os.environ["VOICE_BRIDGE_TOKEN"]
WS = "ws://localhost:8200"
HTTP = "http://localhost:8200"


async def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "tone"
    if mode == "tone":
        t = np.arange(48000 * 2) / 48000
        pcm = (np.sin(2 * np.pi * 440 * t) * 20000).astype(np.int16).tobytes()
    else:
        import pathlib
        # reuse the TTS clip approach from simulate_page
        sys.path.insert(0, str(pathlib.Path(__file__).parent))
        from simulate_page import make_speech_48k_mono
        pcm = await make_speech_48k_mono()

    events: list[dict] = []
    async with websockets.connect(f"{WS}/voice/stream?owner=probe") as stream:
        async def read_stream() -> None:
            async for msg in stream:
                if isinstance(msg, str):
                    events.append(json.loads(msg))

        reader = asyncio.create_task(read_stream())

        async with websockets.connect(f"{WS}/voice/page/audio?token={TOKEN}") as page:
            async with httpx.AsyncClient() as client:
                await client.post(f"{HTTP}/voice/ptt", json={"state": "down", "token": TOKEN})
                await client.post(f"{HTTP}/voice/ptt/heartbeat", json={"token": TOKEN})
            frame = 960 * 2
            for i in range(0, len(pcm), frame):
                await page.send(pcm[i : i + frame])
                await asyncio.sleep(0.02)
            async with httpx.AsyncClient() as client:
                await client.post(f"{HTTP}/voice/ptt", json={"state": "up", "token": TOKEN})
            await asyncio.sleep(0.5)
        reader.cancel()

    audio = [e for e in events if e.get("type") == "audio"]
    speaking = [e for e in events if e.get("type") == "speaking"]
    print(f"audio events: {len(audio)}, speaking events: {[e.get('state') for e in speaking]}")
    if audio:
        pcm_in = base64.b64decode(audio[len(audio) // 2]["pcm"])
        arr = np.frombuffer(pcm_in, dtype=np.int16)
        print(f"mid-clip frame peak amplitude: {np.abs(arr).max()}")


if __name__ == "__main__":
    asyncio.run(main())
