"""Generate the voice session's "thinking" filler clips ("Mm.", "Let's see.").

The clips are pre-generated once with the project's ElevenLabs voice
(TEACHING_AGENT_VOICE_TTS_VOICE_ID from .env) and stored as raw hub-format
PCM (s16le 48 kHz stereo) in out/fillers/. At runtime the conversation
layer plays them while pi is thinking — a courtesy "hold on" signal with
zero per-turn LLM/TTS cost. Regenerate whenever the voice changes.

Usage:
    python tools/make_filler_audio.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from teaching_agent.voice.pcm import mono_24k_to_stereo_48k  # noqa: E402

ENV_FILE = PROJECT_ROOT / ".env"
OUTPUT_DIR = PROJECT_ROOT / "out" / "fillers"

# Varied enough that a repeat doesn't sound like a skipped record,
# short enough that none of them overstay their welcome.
FILLER_LINES = [
    "Mm.",
    "Let's see.",
    "Hm, good question.",
    "One moment.",
    "Mm, let me think on that.",
]


def main() -> int:
    import os

    load_dotenv(dotenv_path=ENV_FILE, override=False)
    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    voice_id = os.environ.get("TEACHING_AGENT_VOICE_TTS_VOICE_ID", "").strip()
    model_id = os.environ.get("TEACHING_AGENT_VOICE_TTS_MODEL", "eleven_turbo_v2_5").strip()
    if not api_key or not voice_id:
        print("ELEVENLABS_API_KEY and TEACHING_AGENT_VOICE_TTS_VOICE_ID are required (.env).")
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream?output_format=pcm_24000"
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}

    for index, line in enumerate(FILLER_LINES, start=1):
        response = httpx.post(
            url, headers=headers, json={"text": line, "model_id": model_id}, timeout=60
        )
        if response.status_code >= 400:
            print(f"ElevenLabs failed for {line!r} ({response.status_code}): {response.text[:200]}")
            return 1
        hub_pcm = mono_24k_to_stereo_48k(response.content)
        path = OUTPUT_DIR / f"filler-{index}.pcm"
        path.write_bytes(hub_pcm)
        print(f"wrote {path.relative_to(PROJECT_ROOT)} — {line!r}")

    print(f"Done. {len(FILLER_LINES)} clips in {OUTPUT_DIR.relative_to(PROJECT_ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
