"""PCM conversion between the hub's wire format and provider formats.

Hub contract (discord-hub/docs/api.md): s16le, 48 kHz, stereo, both ways.
STT providers want narrowband mono; TTS providers return their own rate.
Conversions are deliberately simple (decimate / duplicate) — at speech
quality the difference from filtered resampling is inaudible, and there
is no filter state to get wrong across chunk boundaries.
"""

from __future__ import annotations

import numpy as np


def stereo_48k_to_mono_16k(pcm: bytes) -> bytes:
    """Hub audio frame -> STT feed (drop every third sample, mix channels)."""
    samples = np.frombuffer(pcm, dtype=np.int16)
    if samples.size == 0:
        return b""
    if samples.size % 2:
        samples = samples[:-1]
    mono = samples.reshape(-1, 2).astype(np.int32).mean(axis=1)
    usable = mono.size // 3 * 3
    down = mono[:usable].reshape(-1, 3).mean(axis=1)
    return down.astype(np.int16).tobytes()


def mono_24k_to_stereo_48k(pcm: bytes) -> bytes:
    """TTS output (s16le 24 kHz mono) -> hub wire format (exact 2x upsample)."""
    samples = np.frombuffer(pcm, dtype=np.int16)
    if samples.size == 0:
        return b""
    up = np.repeat(samples, 2)
    stereo = np.empty(up.size * 2, dtype=np.int16)
    stereo[0::2] = up
    stereo[1::2] = up
    return stereo.tobytes()
