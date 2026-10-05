"""Podcast-lecture episodes: the code-owned half of /lecture.

Split of labor (same rule as the rest of the runtime): pi writes the
lecture markdown into lessons/ — that is knowledge-base authoring, its
job. This module does the build work pi is not allowed to do: locate the
file pi says it wrote, render it to audio with the existing tools/
pipeline, and hand back the served path for the link the engine posts.

Pi reports the file it wrote with a directive line, stripped before the
learner ever sees the reply (same pattern as [lesson: ...]):

    [lecture-file: lessons/crash-proofing/lecture.md]

The audio render is a subprocess call into tools/, not a library import:
the tools stay runnable standalone, and a hung TTS render can't wedge
the engine's event loop beyond the timeout.
"""

from __future__ import annotations

import asyncio
import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_DIRECTIVE = re.compile(r"^\[lecture-file:\s*(.+?)\s*\]$", re.IGNORECASE)

_RENDER_SCRIPTS = {
    "elevenlabs": "md_to_audio_elevenlabs.py",
    "edge": "make_audio.py",
}

RENDER_TIMEOUT_SECONDS = 900

# The free pipeline's voice: Andrew is edge-tts's most natural
# conversational voice — closest free thing to podcast narration.
DEFAULT_EDGE_VOICE = "en-US-AndrewNeural"
DEFAULT_EDGE_RATE = "-4%"


class LectureError(RuntimeError):
    """Raised when a lecture episode cannot be produced."""


def split_directive(reply: str) -> tuple[Path | None, str]:
    """Pull the [lecture-file: ...] line out of a pi reply.

    Returns (declared path or None, reply text with the directive removed).
    """
    declared: Path | None = None
    kept: list[str] = []
    for line in reply.splitlines():
        match = _DIRECTIVE.match(line.strip())
        if match is None:
            kept.append(line)
        else:
            declared = Path(match.group(1))
    return declared, "\n".join(kept).strip()


def resolve_lesson_file(knowledge_root: Path, declared: Path) -> Path:
    """Validate pi's declared path: must exist and live under lessons/.

    Pi is prompt-guided, not trusted — a typo'd or escaped path fails here,
    never at the TTS call.
    """
    lessons_root = (knowledge_root / "lessons").resolve()
    candidate = (knowledge_root / declared).resolve()
    if not candidate.is_relative_to(lessons_root):
        raise LectureError(f"declared file is outside lessons/: {declared}")
    if not candidate.is_file():
        raise LectureError(f"declared file does not exist: {declared}")
    return candidate


async def render_lecture_audio(
    source: Path,
    output: Path,
    *,
    tool: str,
    knowledge_root: Path,
    edge_voice: str = DEFAULT_EDGE_VOICE,
    edge_rate: str = DEFAULT_EDGE_RATE,
) -> None:
    """Render lecture markdown to MP3 with the matching tools/ script."""
    script = knowledge_root / "tools" / _RENDER_SCRIPTS[tool]
    if not script.is_file():
        raise LectureError(f"render tool missing: {script}")
    command = [sys.executable, str(script), str(source), "--output", str(output)]
    if tool == "edge":
        # '--rate=-4%' as one arg: a bare '-4%' looks like a flag to argparse.
        command += [f"--voice={edge_voice}", f"--rate={edge_rate}"]
    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=knowledge_root,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        stdout, _ = await asyncio.wait_for(
            process.communicate(), timeout=RENDER_TIMEOUT_SECONDS
        )
    except TimeoutError:
        process.kill()
        raise LectureError(
            f"audio render timed out after {RENDER_TIMEOUT_SECONDS}s"
        ) from None
    if process.returncode != 0:
        tail = (stdout or b"").decode(errors="replace")[-400:]
        raise LectureError(f"audio render failed ({process.returncode}): {tail}")
    if not output.is_file():
        raise LectureError(f"audio render produced no file: {output}")
    logger.info("Lecture audio rendered: %s", output)
