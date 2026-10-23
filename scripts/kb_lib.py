"""Shared internals for the knowledge-log CLIs (kb_append / kb_derive /
kb_migrate). Source of truth = append-only, hash-chained JSONL event logs in
the kb directory; everything else is derived and regenerable. See
docs/proposals/knowledge-storage.md, "Adopted design (2026-10-21)".
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

LEVELS = ["presented", "recognized", "recalled", "explained", "applied", "transferred"]

EVENT_TYPES = {
    "evidence",
    "node_created",
    "node_split",
    "node_merge",
    "claim_asserted",
    "claim_rechecked",
    "routing_override",
    "migration_flag",
}

EVIDENCE_REQUIRED = ("ts", "node", "level", "delay_days", "coached")


class KBError(Exception):
    """Validation or integrity failure; CLIs turn this into a nonzero exit."""


def canonical(event: dict) -> str:
    return json.dumps(event, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_line(raw_line: str) -> str:
    return hashlib.sha256(raw_line.encode("utf-8")).hexdigest()


def validate_event(event: dict) -> None:
    etype = event.get("type")
    if etype not in EVENT_TYPES:
        raise KBError(f"unknown event type: {etype!r}")
    if etype == "evidence":
        for field in EVIDENCE_REQUIRED:
            if field not in event:
                raise KBError(f"evidence event missing field: {field}")
        if event["level"] not in LEVELS:
            raise KBError(f"unknown level: {event['level']!r}")
        if not isinstance(event["delay_days"], (int, float)) or event["delay_days"] < 0:
            raise KBError("delay_days must be a non-negative number")
        if not isinstance(event["coached"], bool):
            raise KBError("coached must be a boolean")
    elif etype == "node_created":
        if "node" not in event or "statement" not in event:
            raise KBError("node_created requires node and statement")
        if "edges" in event and not isinstance(event["edges"], list):
            raise KBError("edges must be a list")
    elif etype == "migration_flag":
        if event.get("unverified") is not True:
            raise KBError("migration_flag must carry unverified: true")


def log_path(kb: Path, name: str = "events") -> Path:
    return kb / f"{name}.jsonl"


def read_raw_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def verify_chain(path: Path) -> list[dict]:
    """Parse the log and verify the hash chain. Raises KBError on tampering."""
    lines = read_raw_lines(path)
    events = []
    for i, raw in enumerate(lines):
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise KBError(f"line {i + 1} is not valid JSON") from exc
        expected_prev = None if i == 0 else sha256_line(lines[i - 1])
        if event.get("prev") != expected_prev:
            raise KBError(
                f"hash chain broken at line {i + 1}: history was rewritten; refusing to write"
            )
        events.append(event)
    return events


def append_event(kb: Path, event: dict) -> None:
    """The ONLY write path. Validates, verifies the chain, then appends."""
    validate_event(event)
    kb.mkdir(parents=True, exist_ok=True)
    path = log_path(kb)
    lines = read_raw_lines(path)
    if lines:
        # verify_chain raises if history was tampered with — nothing is written.
        verify_chain(path)
        prev = sha256_line(lines[-1])
    else:
        prev = None
    record = dict(event)
    record["v"] = 1
    record["prev"] = prev
    with path.open("a", encoding="utf-8") as fh:
        fh.write(canonical(record) + "\n")


def load_events(kb: Path) -> list[dict]:
    return verify_chain(log_path(kb))
