"""Turn a Markdown document into a single MP3 using the project's ElevenLabs voice.

Uses the same voice identity as the live agent (TEACHING_AGENT_VOICE_TTS_VOICE_ID —
"George", our Alfred) from .env, so the audio matches what the #learning channel
already knows. Reuses the Markdown cleanup rules from tools/make_audio.py but
synthesizes with ElevenLabs instead of edge-tts.

Usage:
    python tools/md_to_audio_elevenlabs.py "C:/path/to/document.md" [--output out.mp3]
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# ElevenLabs rejects very large single requests; stay comfortably under the limit.
MAX_CHARS_PER_REQUEST = 4000


def markdown_to_speech(markdown: str) -> str:
    """Remove visual Markdown while retaining readable spoken structure."""
    text = re.sub(r"```.*?```", "", markdown, flags=re.DOTALL)
    text = re.sub(r"^---+$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+[.)]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"!\[([^]]*)]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", text)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    text = text.replace("├──", "").replace("└──", "").replace("│", "")
    text = text.replace("→", " then ").replace("↓", " then ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def chunk_text(text: str, max_chars: int = MAX_CHARS_PER_REQUEST) -> list[str]:
    """Split on paragraph boundaries, packing paragraphs up to max_chars."""
    chunks: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        # A single oversized paragraph gets hard-split on sentence-ish boundaries.
        while len(paragraph) > max_chars:
            cut = paragraph.rfind(". ", 0, max_chars)
            if cut < max_chars // 2:
                cut = max_chars
            else:
                cut += 1
            chunks.append(paragraph[:cut].strip())
            paragraph = paragraph[cut:].strip()
        current = paragraph
    if current:
        chunks.append(current)
    return chunks


def synthesize(text: str, *, api_key: str, voice_id: str, model_id: str) -> bytes:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128"
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    body = {"text": text, "model_id": model_id}
    with httpx.Client(timeout=120) as client:
        response = client.post(url, headers=headers, json=body)
    if response.status_code >= 400:
        raise SystemExit(
            f"ElevenLabs failed ({response.status_code}): {response.content[:300]!r}"
        )
    return response.content


def read_env(name: str) -> str:
    import os

    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"{name} is missing from {ENV_FILE}")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synthesize a Markdown document to MP3 with the project's ElevenLabs voice."
    )
    parser.add_argument("source", type=Path, help="Path to the Markdown document")
    parser.add_argument("--output", type=Path, help="MP3 output path")
    parser.add_argument("--transcript", type=Path, help="Spoken-text transcript output path")
    parser.add_argument("--voice-id", help="Override the .env voice id")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_dotenv(ENV_FILE)
    api_key = read_env("ELEVENLABS_API_KEY")
    voice_id = args.voice_id or read_env("TEACHING_AGENT_VOICE_TTS_VOICE_ID")
    model_id = read_env("TEACHING_AGENT_VOICE_TTS_MODEL")

    source = args.source.resolve()
    if not source.is_file():
        raise SystemExit(f"Source does not exist: {source}")

    output_path = (args.output or PROJECT_ROOT / "out" / f"{source.stem}.mp3").resolve()
    transcript_path = (
        args.transcript or output_path.with_suffix(".transcript.txt")
    ).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    transcript_path.parent.mkdir(parents=True, exist_ok=True)

    speech_text = markdown_to_speech(source.read_text(encoding="utf-8"))
    transcript_path.write_text(speech_text, encoding="utf-8")

    chunks = chunk_text(speech_text)
    print(f"Synthesizing {len(speech_text):,} chars in {len(chunks)} request(s)…")
    with output_path.open("wb") as out:
        for index, chunk in enumerate(chunks, start=1):
            print(f"  chunk {index}/{len(chunks)} ({len(chunk):,} chars)")
            out.write(synthesize(chunk, api_key=api_key, voice_id=voice_id, model_id=model_id))
            if index < len(chunks):
                time.sleep(1)  # be gentle with rate limits

    words = len(speech_text.split())
    print(f"Transcript: {transcript_path}")
    print(f"Audio: {output_path}")
    print(f"Words: {words:,} (about {words / 145:.1f} minutes at 145 words/minute)")


if __name__ == "__main__":
    sys.exit(main())
