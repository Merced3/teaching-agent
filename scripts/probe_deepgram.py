"""Probe: feed the TTS clip straight to Deepgram (no bridge) and print
every message — isolates Deepgram+conversion from the bridge transport."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

load_dotenv(".env")

import numpy as np
from simulate_page import make_speech_48k_mono
from teaching_agent.voice.stt import DeepgramSTT

logging.basicConfig(level=logging.INFO)


def mono_48k_to_16k(pcm: bytes) -> bytes:
    samples = np.frombuffer(pcm, dtype=np.int16).astype(np.int32)
    usable = samples.size // 3 * 3
    return samples[:usable].reshape(-1, 3).mean(axis=1).astype(np.int16).tobytes()


async def main() -> None:
    speech48 = await make_speech_48k_mono()
    pcm16 = mono_48k_to_16k(speech48)
    print(f"clip: {len(pcm16) / 32000:.1f}s at 16kHz, peak {np.abs(np.frombuffer(pcm16, dtype=np.int16)).max()}")

    stt = DeepgramSTT(os.environ["DEEPGRAM_API_KEY"])
    stt.on_utterance = lambda t: print("UTTERANCE:", t)
    await stt.start()

    frame = 320 * 2  # 20 ms at 16 kHz
    for i in range(0, len(pcm16), frame):
        stt.feed(pcm16[i : i + frame])
        await asyncio.sleep(0.02)
    await asyncio.sleep(2)
    stt.finalize()
    await asyncio.sleep(5)
    await stt.stop()
    print("done")


if __name__ == "__main__":
    asyncio.run(main())
