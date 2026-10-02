"""Raw Deepgram probe: print every message the socket sends back."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import websockets
from dotenv import load_dotenv

load_dotenv(".env")

from probe_deepgram import mono_48k_to_16k
from simulate_page import make_speech_48k_mono

URL = (
    "wss://api.deepgram.com/v1/listen"
    "?model=nova-3&encoding=linear16&sample_rate=16000&channels=1"
    "&interim_results=true&endpointing=900&smart_format=true&vad_events=true"
)


async def main() -> None:
    pcm16 = mono_48k_to_16k(await make_speech_48k_mono())
    async with websockets.connect(
        URL,
        additional_headers={"Authorization": f"Token {os.environ['DEEPGRAM_API_KEY']}"},
    ) as ws:
        async def reader() -> None:
            async for raw in ws:
                print("DG >>", raw[:400])

        task = asyncio.create_task(reader())
        frame = 320 * 2
        for i in range(0, len(pcm16), frame):
            await ws.send(pcm16[i : i + frame])
            await asyncio.sleep(0.02)
        await ws.send(json.dumps({"type": "Finalize"}))
        await asyncio.sleep(5)
        await ws.send(json.dumps({"type": "CloseStream"}))
        await asyncio.sleep(2)
        task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
