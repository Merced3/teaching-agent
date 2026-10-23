#!/usr/bin/env python3
"""kb_append.py — the ONLY way events are written to the knowledge log.

Usage:
    python scripts/kb_append.py --kb KBDIR append --event '{"type": "evidence", ...}'

Validates the event schema, verifies the hash chain over kb/events.jsonl,
and appends the event with `prev` = sha256 of the previous raw line. Any
rewrite of history breaks the chain and the write is refused (nonzero
exit, log untouched). The log is a write boundary: pi never edits the log
files directly.

See docs/proposals/knowledge-storage.md, "Adopted design (2026-10-21)".
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kb_lib import KBError, append_event


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kb", required=True, type=Path, help="knowledge base directory")
    sub = parser.add_subparsers(dest="command", required=True)
    app = sub.add_parser("append", help="append one event")
    app.add_argument("--event", required=True, help="event as a JSON object")
    args = parser.parse_args(argv)

    try:
        event = json.loads(args.event)
    except json.JSONDecodeError as exc:
        print(f"error: --event is not valid JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(event, dict):
        print("error: --event must be a JSON object", file=sys.stderr)
        return 2

    try:
        append_event(args.kb, event)
    except KBError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
