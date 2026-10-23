#!/usr/bin/env python3
"""kb_migrate.py — turn prose history ("Prior:" chains, session logs) into
candidate knowledge-log events.

Usage:
    python scripts/kb_migrate.py --kb KBDIR --source path/to/history.md

Migration honesty: anything that does not parse cleanly into exactly one
node + one evidence level is recorded as a `migration_flag` event with
`unverified: true` — flagged for human review, never guessed. Confident
parses become ordinary `evidence` events (channel "migration").

Heuristics (deliberately conservative):
- one event per "Prior:" entry, only when the entry names exactly ONE node
  and ONE unambiguous evidence level;
- "recalled unaided" / "explained unaided" / "transferred" → unaided levels;
- "faded ... re-presented" → recognized, coached (a fade is not evidence of
  knowing; the re-presentation is presented-grade evidence at best);
- delay is extracted as a number ("~6 WEEKS" → 42, "~3 days" → 3,
  "same-day" → 0) — a dimension, never folded into the level.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kb_lib import KBError, append_event

# Keyword aliases → node ids. First matching group wins; aliases within a
# group all resolve to the same node (so "node 2 transactions — ATOMICITY"
# is one node, not two).
NODE_ALIASES: list[tuple[str, tuple[str, ...]]] = [
    ("sd/crash-window", ("crash window", "crash-window")),
    ("sd/atomicity", ("atomicity", "atomic", "transactions")),
    ("sd/write-boundary", ("write boundary", "write-boundary")),
    ("sd/invariant", ("invariant",)),
    ("sd/state-machine", ("state machine", "state-machine")),
    ("sd/keyed-receipt", ("keyed receipt", "keyed-receipt", "receipt")),
    ("sd/idempotency", ("idempoten", "retry-safe", "retry safe")),
    ("sd/backoff", ("backoff",)),
    ("sd/jitter", ("jitter",)),
    ("sd/thundering-herd", ("thundering herd", "thundering-herd")),
    ("sd/reconciliation-job", ("reconciliation job", "reconciliation-job")),
    ("sd/timeout-unknown-state", ("timeout", "unknown state", "unknown-state")),
]

# (regex, level, coached). Evaluated in order; first match per entry.
LEVEL_PATTERNS: list[tuple[re.Pattern[str], str, bool]] = [
    (re.compile(r"recalled unaided", re.I), "recalled", False),
    (re.compile(r"explained unaided|derived (it |mostly )?unaided", re.I), "explained", False),
    (re.compile(r"\btransferred\b", re.I), "transferred", False),
    (re.compile(r"\bfaded\b", re.I), "recognized", True),
    (re.compile(r"\bcoached\b", re.I), "recognized", True),
    (re.compile(r"\brecognized\b", re.I), "recognized", True),
]

DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
PRIOR_RE = re.compile(r"^Prior\b", re.I)

DELAY_PATTERNS = [
    re.compile(r"~?\s*(\d+)\s*[- ]weeks?\b", re.I),
    re.compile(r"~?\s*(\d+)\s*[- ]days?\b", re.I),
]


def find_nodes(text: str) -> list[str]:
    lower = text.lower()
    return [node for node, aliases in NODE_ALIASES if any(a in lower for a in aliases)]


def find_level(text: str) -> tuple[str, bool] | None:
    for pattern, level, coached in LEVEL_PATTERNS:
        if pattern.search(text):
            return level, coached
    return None


def find_delay_days(text: str) -> int:
    for pattern, factor in ((DELAY_PATTERNS[0], 7), (DELAY_PATTERNS[1], 1)):
        match = pattern.search(text)
        if match:
            return int(match.group(1)) * factor
    return 0


def migrate_entry(entry: str, source: str) -> dict:
    """Return one event dict for a Prior: entry (evidence or migration_flag)."""
    date = DATE_RE.search(entry)
    nodes = find_nodes(entry)
    level = find_level(entry)

    def flag(reason: str) -> dict:
        return {
            "type": "migration_flag",
            "ts": f"{date.group(1)}T00:00:00Z" if date else None,
            "unverified": True,
            "source": source,
            "reason": reason,
            "excerpt": entry.strip()[:500],
        }

    if not date:
        return flag("no date found")
    if len(nodes) != 1:
        return flag(f"expected exactly one node, found {len(nodes)}: {nodes}")
    if level is None:
        return flag("no unambiguous evidence level found")

    lvl, coached = level
    return {
        "type": "evidence",
        "ts": f"{date.group(1)}T00:00:00Z",
        "node": nodes[0],
        "level": lvl,
        "delay_days": find_delay_days(entry),
        "coached": coached,
        "channel": "migration",
        "session": source,
        "notes": entry.strip()[:500],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kb", required=True, type=Path, help="knowledge base directory")
    parser.add_argument("--source", required=True, type=Path, help="prose file to migrate")
    args = parser.parse_args(argv)

    text = args.source.read_text(encoding="utf-8")
    entries = [line for line in text.splitlines() if PRIOR_RE.match(line.strip())]
    if not entries:
        print(f"error: no 'Prior:' entries found in {args.source}", file=sys.stderr)
        return 2

    migrated = flagged = 0
    try:
        for entry in entries:
            event = migrate_entry(entry, str(args.source))
            append_event(args.kb, event)
            if event["type"] == "migration_flag":
                flagged += 1
            else:
                migrated += 1
    except KBError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"migrated {migrated} evidence event(s), flagged {flagged} for review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
