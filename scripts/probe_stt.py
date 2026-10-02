"""Probe: run bridge-forwarded audio through the agent's own STT path.

Attaches as consumer, plays the page with real speech, then feeds every
audio event through stereo_48k_to_mono_16k -> DeepgramSTT, exactly like
VoiceConversation does. Prints any utterances produced.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import sys
from pathlib import Path

import httpx
import websockets
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from simulate_page import make_speech_48k_mono
from teaching_agent.voice.pcm import stereo_48k_to_mono_16k
from teaching_agent.voice.stt import DeepgramSTT

load_dotenv("../voice-bridge/.env")
TOKEN = os.environ["VOICE_BRIDGE_TOKEN"]
load_dotenv(".env", override=False)

WS = "ws://localhost:8200"
HTTP = "http://localhost:8200"


async def main() -> None:
    speech = await make_speech_48k_mono()
    stt = DeepgramSTT(os.environ["DEEPGRAM_API_KEY"])
    utterances: list[str] = []
    stt.on_utterance = lambda t: (utterances.append(t), print("UTTERANCE:", t))
    await stt.start()

    fed = 0
    async with websockets.connect(f"{WS}/voice/stream?owner=probe-stt") as stream:
        async def read_stream() -> None:
            nonlocal fed
            async for msg in stream:
                if isinstance(msg, str):
                    e = json.loads(msg)
                    if e.get("type") == "audio":
                        stt.feed(stereo_48k_to_mono_16k(base64.b64decode(e["pcm"])))
                        fed += 1

        reader = asyncio.create_task(read_stream())
        async with websockets.connect(f"{WS}/voice/page/audio?token={TOKEN}") as page:
            async with httpx.AsyncClient() as client:
                await client.post(f"{HTTP}/voice/ptt", json={"state": "down", "token": TOKEN})
            frame = 960 * 2
            for i in range(0, len(speech), frame):
                await page.send(speech[i : i + frame])
                await asyncio.sleep(0.02)
            async with httpx.AsyncClient() as client:
                await client.post(f"{HTTP}/voice/ptt", json={"state": "up", "token": TOKEN})
        await asyncio.sleep(2)
        stt.finalize()
        await asyncio.sleep(4)
        reader.cancel()

    await stt.stop()
    print(f"audio events fed to STT: {fed}; utterances: {utterances}")


if __name__ == "__main__":
    asyncio.run(main())
