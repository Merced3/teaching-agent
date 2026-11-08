"""Operational-state backends: local JSON for tests, managed Postgres in production."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Protocol

import psycopg
from psycopg.types.json import Jsonb

from .migrate import upgrade

logger = logging.getLogger(__name__)


class StateStore(Protocol):
    def load(self, key: str) -> Any | None: ...
    def save(self, key: str, payload: Any) -> None: ...
    def delete(self, key: str) -> None: ...


class JsonStateStore:
    """One JSON document per legacy path; preserves offline/test behavior."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self, key: str) -> Any | None:
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def save(self, key: str, payload: Any) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def delete(self, key: str) -> None:
        self._path.unlink(missing_ok=True)


class PostgresStateStore:
    """Small mutable operational documents, keyed by their former file stem."""

    def __init__(self, database_url: str, *, initialize: bool = True) -> None:
        self._url = database_url
        if initialize:
            upgrade("teaching", database_url)

    def load(self, key: str) -> Any | None:
        with psycopg.connect(self._url) as conn:
            row = conn.execute(
                "SELECT payload FROM operational_state WHERE key = %s", (key,)
            ).fetchone()
        return row[0] if row else None

    def save(self, key: str, payload: Any) -> None:
        with psycopg.connect(self._url) as conn:
            conn.execute(
                """INSERT INTO operational_state (key, payload) VALUES (%s, %s)
                   ON CONFLICT (key) DO UPDATE SET payload = EXCLUDED.payload,
                   updated_at = now()""",
                (key, Jsonb(payload)),
            )

    def delete(self, key: str) -> None:
        with psycopg.connect(self._url) as conn:
            conn.execute("DELETE FROM operational_state WHERE key = %s", (key,))


def operational_store(path: Path, database_url: str | None) -> StateStore:
    return PostgresStateStore(database_url) if database_url else JsonStateStore(path)


def state_key(path: Path) -> str:
    return path.stem
