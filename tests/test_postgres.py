"""Opt-in managed-Postgres integration tests.

Normal CI stays offline. Set TEACHING_AGENT_TEST_POSTGRES_URL and
KNOWLEDGE_TEST_DATABASE_URL to empty databases whose users may create/drop
schemas; every test uses its own schema and never touches public tables.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import uuid4

import psycopg
import pytest

from teaching_agent.migrate import upgrade
from teaching_agent.storage import PostgresStateStore

REPO = Path(__file__).resolve().parent.parent


def _schema_url(url: str, schema: str) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query))
    query["options"] = f"-csearch_path={schema}"
    return urlunsplit(parts._replace(query=urlencode(query)))


@pytest.fixture
def postgres_schema(request: pytest.FixtureRequest) -> str:
    marker = request.node.get_closest_marker("database")
    env_name = marker.args[0] if marker else "TEACHING_AGENT_TEST_POSTGRES_URL"
    base_url = os.environ.get(env_name, "").strip()
    if not base_url:
        pytest.skip(f"{env_name} not configured")
    schema = f"test_{uuid4().hex}"
    with psycopg.connect(base_url) as conn:
        conn.execute(f'CREATE SCHEMA "{schema}"')
    try:
        yield schema
    finally:
        with psycopg.connect(base_url) as conn:
            conn.execute(f'DROP SCHEMA "{schema}" CASCADE')


@pytest.mark.database("TEACHING_AGENT_TEST_POSTGRES_URL")
def test_operational_state_round_trip(postgres_schema: str) -> None:
    url = _schema_url(os.environ["TEACHING_AGENT_TEST_POSTGRES_URL"], postgres_schema)
    upgrade("teaching", url)
    store = PostgresStateStore(url)
    assert store.load("pings") is None
    store.save("pings", {"pings_per_day": 3, "last_fired": None})
    assert store.load("pings")["pings_per_day"] == 3
    store.delete("pings")
    assert store.load("pings") is None


@pytest.mark.database("KNOWLEDGE_TEST_DATABASE_URL")
def test_postgres_kb_behaviors_and_export(
    postgres_schema: str, tmp_path: Path
) -> None:
    url = _schema_url(os.environ["KNOWLEDGE_TEST_DATABASE_URL"], postgres_schema)
    upgrade("knowledge", url)
    kb = tmp_path / "kb"
    env = os.environ.copy()
    env["KNOWLEDGE_DATABASE_URL"] = url

    def run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(REPO / "scripts" / script), *args],
            cwd=REPO, env=env, capture_output=True, text=True,
        )

    event = json.dumps({
        "type": "evidence", "ts": "2026-10-21T12:00:00Z",
        "node": "sd/atomicity", "level": "recalled", "delay_days": 6,
        "coached": False, "channel": "test", "session": "test", "notes": "",
    })
    refused = run("kb_append.py", "--kb", str(kb), "append", "--event", event)
    assert refused.returncode != 0 and "--init" in refused.stderr
    initialized = run("kb_append.py", "--kb", str(kb), "append", "--event", event, "--init")
    duplicate_init = run(
        "kb_append.py", "--kb", str(kb), "append", "--event", event, "--init"
    )
    assert initialized.returncode == 0
    assert duplicate_init.returncode != 0
    assert run("kb_append.py", "--kb", str(kb), "append", "--event", event).returncode == 0

    exported = tmp_path / "events.jsonl"
    result = run("kb_derive.py", "--kb", str(kb), "export-jsonl", "--out", str(exported))
    assert result.returncode == 0, result.stderr
    lines = exported.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[1])["prev"] is not None

    grades = run("kb_derive.py", "--kb", str(kb), "grades")
    assert grades.returncode == 0, grades.stderr
    assert json.loads(grades.stdout)["sd/atomicity"]["retention"] is True

    with psycopg.connect(url) as conn:
        with pytest.raises(psycopg.Error):
            conn.execute("UPDATE events SET node = 'tampered' WHERE id = 1")
        conn.rollback()
        with pytest.raises(psycopg.errors.RaiseException):
            conn.execute(
                "INSERT INTO events (id, event_type, payload, raw_line, prev) "
                "VALUES (3, 'evidence', '{}'::jsonb, '{}', 'bad')"
            )
