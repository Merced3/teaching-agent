"""Guarded evidence boundary for append-only, hash-chained knowledge events.

Production selects Postgres with KNOWLEDGE_DATABASE_URL. Offline development
keeps the JSONL backend; both enforce the same schema, derivation, chain, and
explicit-genesis behavior. Postgres stores the original canonical raw line so
nightly JSONL exports preserve every historical hash link exactly.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

LEVELS = ["presented", "recognized", "recalled", "explained", "applied", "transferred"]

EVENT_TYPES = {
    "evidence", "node_created", "node_split", "node_merge", "claim_asserted",
    "claim_rechecked", "routing_override", "migration_flag",
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
    elif etype == "migration_flag" and event.get("unverified") is not True:
        raise KBError("migration_flag must carry unverified: true")


def log_path(kb: Path, name: str = "events") -> Path:
    return kb / f"{name}.jsonl"


def read_raw_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def verify_raw_lines(lines: list[str]) -> list[dict]:
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


def verify_chain(path: Path) -> list[dict]:
    return verify_raw_lines(read_raw_lines(path))


def configured_database_url() -> str | None:
    return os.environ.get("KNOWLEDGE_DATABASE_URL", "").strip() or None


def knowledge_exists(kb: Path, database_url: str | None = None) -> bool:
    url = database_url or configured_database_url()
    if not url:
        return log_path(kb).exists()
    try:
        with psycopg.connect(url) as conn:
            return bool(conn.execute("SELECT count(*) FROM events").fetchone()[0])
    except psycopg.Error as exc:
        raise KBError(f"cannot inspect Postgres knowledge events: {exc}") from exc


def _read_postgres_lines(conn: psycopg.Connection) -> list[str]:
    return [row[0] for row in conn.execute("SELECT raw_line FROM events ORDER BY id")]


def _event_ts(event: dict) -> datetime | None:
    value = event.get("ts")
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise KBError(f"invalid event timestamp: {value!r}") from exc


def _insert_postgres(conn: psycopg.Connection, event_id: int, event: dict, raw: str) -> None:
    conn.execute(
        """INSERT INTO events (id, event_type, node, event_ts, payload, raw_line, prev)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (
            event_id, event.get("type"), event.get("node"), _event_ts(event),
            Jsonb(event), raw, event.get("prev"),
        ),
    )


def append_event(kb: Path, event: dict, database_url: str | None = None) -> None:
    """The only ordinary event write path, on either configured backend."""
    validate_event(event)
    url = database_url or configured_database_url()
    if url:
        try:
            with psycopg.connect(url) as conn:
                # Serializes appends under PgBouncer transaction pooling.
                conn.execute("LOCK TABLE events IN EXCLUSIVE MODE")
                lines = _read_postgres_lines(conn)
                verify_raw_lines(lines)
                record = dict(event)
                record["v"] = 1
                record["prev"] = sha256_line(lines[-1]) if lines else None
                raw = canonical(record)
                _insert_postgres(conn, len(lines) + 1, record, raw)
        except psycopg.Error as exc:
            raise KBError(f"Postgres knowledge append refused: {exc}") from exc
        return

    kb.mkdir(parents=True, exist_ok=True)
    path = log_path(kb)
    lines = read_raw_lines(path)
    verify_raw_lines(lines)
    record = dict(event)
    record["v"] = 1
    record["prev"] = sha256_line(lines[-1]) if lines else None
    with path.open("a", encoding="utf-8") as fh:
        fh.write(canonical(record) + "\n")


def import_jsonl(source: Path, database_url: str) -> dict:
    """One-time, empty-destination import preserving raw lines and event ids."""
    lines = read_raw_lines(source)
    events = verify_raw_lines(lines)
    try:
        with psycopg.connect(database_url) as conn:
            conn.execute("LOCK TABLE events IN EXCLUSIVE MODE")
            if _read_postgres_lines(conn):
                raise KBError("Postgres knowledge DB is not empty; import refused")
            for event_id, (event, raw) in enumerate(zip(events, lines, strict=True), 1):
                _insert_postgres(conn, event_id, event, raw)
            imported_lines = _read_postgres_lines(conn)
            verify_raw_lines(imported_lines)
            if imported_lines != lines:
                raise KBError("Postgres raw-line verification differs from source")
            nodes = conn.execute("SELECT count(*) FROM nodes").fetchone()[0]
    except psycopg.Error as exc:
        raise KBError(f"Postgres knowledge import failed: {exc}") from exc
    return {
        "events": len(lines), "nodes": nodes,
        "bytes": source.stat().st_size,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "canonical_sha256": hashlib.sha256(("\n".join(lines) + "\n").encode()).hexdigest(),
    }


def load_events(kb: Path, database_url: str | None = None) -> list[dict]:
    url = database_url or configured_database_url()
    if url:
        try:
            with psycopg.connect(url) as conn:
                return verify_raw_lines(_read_postgres_lines(conn))
        except psycopg.Error as exc:
            raise KBError(f"Postgres knowledge read failed: {exc}") from exc
    return verify_chain(log_path(kb))


def export_jsonl(kb: Path, destination: Path) -> dict:
    """Write a deterministic portable export after authoritative verification."""
    url = configured_database_url()
    if not url:
        raise KBError("KNOWLEDGE_DATABASE_URL is required for export-jsonl")
    try:
        with psycopg.connect(url) as conn:
            lines = _read_postgres_lines(conn)
    except psycopg.Error as exc:
        raise KBError(f"Postgres knowledge export failed: {exc}") from exc
    events = verify_raw_lines(lines)
    payload = "\n".join(lines) + ("\n" if lines else "")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(payload, encoding="utf-8", newline="\n")
    return {
        "events": len(events),
        "nodes": sum(e.get("type") == "node_created" for e in events),
        "bytes": len(payload.encode("utf-8")),
        "sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
    }
