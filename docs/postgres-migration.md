# Postgres + R2 data migration

Owner-approved P2c decision: the project-independent `knowledge` database is the
append-only knowledge source of truth. `teaching` holds mutable operational JSON;
`harness_teaching` holds harness state; generated audio is in
`automations-teaching` R2. Curated markdown remains in git. Pi JSONL transcripts
are working memory: close open sessions before a host redeploy and retain old
files read-only; they are not synchronized to R2.

## Safety and compatibility

Normal tests use temporary JSON/JSONL and need no services. The original four
knowledge behavior tests and the explicit-genesis regression remain unchanged.
Opt-in tests in `tests/test_postgres.py` create random isolated schemas and drop
them afterward; never point them at a populated public schema.

`knowledge.events` stores stable sequential event IDs, exact canonical raw lines,
JSONB payloads, event types/nodes, UTC timestamps, and `prev`. A database trigger
checks each new link using SHA-256; separate triggers reject UPDATE/DELETE, and
the application role's mutation grants are revoked. `nodes` is the current
registered-node projection. `kb_append.py` remains the only ordinary write path.

## Apply schemas and test

Run from the deploy clone with dependencies installed. Credentials come from
`/opt/automations/env/data-platform.env` and are never command arguments.

```bash
set -a; source /opt/automations/env/data-platform.env; set +a
python -m teaching_agent.migrate knowledge --url-env KNOWLEDGE_DATABASE_URL
python -m teaching_agent.migrate teaching --url-env TEACHING_AGENT_DATABASE_URL

export KNOWLEDGE_TEST_DATABASE_URL="$KNOWLEDGE_DATABASE_URL"
export TEACHING_AGENT_TEST_POSTGRES_URL="$TEACHING_AGENT_DATABASE_URL"
pytest tests/test_postgres.py -v
```

The integration fixtures create/drop random schemas, so they do not touch the
production `public` schema. Run these before importing production rows.

## Copy and prove

Stop teaching-agent so mutable sources cannot change. Use the authoritative
Droplet JSONL, never the laptop checkout:

```bash
python scripts/kb_append.py --kb /opt/automations/kb/teaching-agent/kb \
  import-jsonl --source /opt/automations/kb/teaching-agent/kb/events.jsonl --init
python -m teaching_agent.migrate_data \
  --data-dir /opt/automations/data/teaching-agent \
  --assets-root /opt/automations/kb/teaching-agent
```

The knowledge import requires an empty DB, verifies the source and destination
with the authoritative chain implementation, preserves raw lines and IDs, and
reports counts/checksums. Operational copy refuses nonempty destination keys and
compares canonical payloads. R2 copy downloads every uploaded object and compares
its bytes and SHA-256. Sources are never modified.

Export and verify the portable snapshot at any time:

```bash
python scripts/kb_derive.py --kb /opt/automations/kb/teaching-agent/kb \
  export-jsonl --out /opt/automations/kb/teaching-agent/kb/events.jsonl
```

The nightly `kb-snapshot.sh` performs this export before its git snapshot;
`kb-push.sh` pushes it. JSONL is now a portable export, not a second write target.

## Harness state

Apply the harness's own Alembic migration, then use its read-only SQLite merger
with `HARNESS_DATABASE_URL`. Keep the Droplet and laptop provenance distinct;
merge only reviewed local-only rows. Production startup reads the same URL.
Pi session files and disposable logs/status files are not durable migration
inputs.

## Cutover and deletion gate

Copy `TEACHING_AGENT_DATABASE_URL`, `KNOWLEDGE_DATABASE_URL`,
`HARNESS_DATABASE_URL`, and the five `TEACHING_AGENT_R2_*` values into the
server-only teaching-agent env. Deploy, then verify a real ping and a real
`/close`, event/session counts, export checksum, and error logs.

Keep every old JSON/JSONL/SQLite/pi-session source unchanged and read-only until
the ops deletion gate: subsequent managed backup, encrypted R2 dump and restore
drill, read-only interval, recorded verification, and explicit owner approval.
No source deletion is part of this migration.
