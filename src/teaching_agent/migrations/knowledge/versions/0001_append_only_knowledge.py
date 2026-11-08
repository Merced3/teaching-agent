"""Hash-chained, append-only private knowledge events and node projection."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_append_only_knowledge"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("node", sa.Text()),
        sa.Column("event_ts", sa.DateTime(timezone=True)),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("raw_line", sa.Text(), nullable=False),
        sa.Column("prev", sa.Text()),
        sa.CheckConstraint("id > 0", name="events_positive_id"),
        sa.CheckConstraint("prev IS NULL OR prev ~ '^[0-9a-f]{64}$'", name="events_prev_sha256"),
        sa.UniqueConstraint("raw_line", name="events_raw_line_unique"),
    )
    op.create_index("events_type_id", "events", ["event_type", "id"])
    op.create_index("events_node_id", "events", ["node", "id"])
    op.create_table(
        "nodes",
        sa.Column("node", sa.Text(), primary_key=True),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("edges", postgresql.JSONB(), nullable=False),
        sa.Column("created_event_id", sa.BigInteger(), sa.ForeignKey("events.id"),
                  nullable=False, unique=True),
    )
    op.execute("""
        CREATE FUNCTION knowledge_event_before_insert() RETURNS trigger AS $$
        DECLARE previous events%ROWTYPE;
        BEGIN
            IF NEW.id = 1 THEN
                IF NEW.prev IS NOT NULL OR NEW.payload->>'prev' IS NOT NULL THEN
                    RAISE EXCEPTION 'genesis event must have null prev';
                END IF;
            ELSE
                SELECT * INTO previous FROM events WHERE id = NEW.id - 1;
                IF previous.id IS NULL THEN
                    RAISE EXCEPTION 'event ids must be contiguous; missing %', NEW.id - 1;
                END IF;
                IF NEW.prev IS DISTINCT FROM encode(digest(previous.raw_line, 'sha256'), 'hex')
                   OR NEW.payload->>'prev' IS DISTINCT FROM NEW.prev THEN
                    RAISE EXCEPTION 'knowledge hash chain mismatch at event %', NEW.id;
                END IF;
            END IF;
            IF NEW.event_type = 'node_created' THEN
                INSERT INTO nodes (node, statement, edges, created_event_id)
                VALUES (NEW.node, NEW.payload->>'statement',
                        COALESCE(NEW.payload->'edges', '[]'::jsonb), NEW.id);
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE FUNCTION knowledge_append_only() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'knowledge records are append-only';
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute(
        "CREATE TRIGGER events_chain BEFORE INSERT ON events FOR EACH ROW "
        "EXECUTE FUNCTION knowledge_event_before_insert()"
    )
    op.execute(
        "CREATE TRIGGER events_no_mutation BEFORE UPDATE OR DELETE ON events "
        "FOR EACH ROW EXECUTE FUNCTION knowledge_append_only()"
    )
    op.execute(
        "CREATE TRIGGER nodes_no_mutation BEFORE UPDATE OR DELETE ON nodes "
        "FOR EACH ROW EXECUTE FUNCTION knowledge_append_only()"
    )
    # The application uses the same-named non-superuser login. Revoke its own
    # mutation grants as defense in depth; the triggers also reject owner DML.
    op.execute("REVOKE UPDATE, DELETE, TRUNCATE ON events FROM CURRENT_USER")
    op.execute("REVOKE UPDATE, DELETE, TRUNCATE ON nodes FROM CURRENT_USER")


def downgrade() -> None:
    op.execute("DROP TABLE nodes CASCADE")
    op.execute("DROP TABLE events CASCADE")
    op.execute("DROP FUNCTION IF EXISTS knowledge_append_only()")
    op.execute("DROP FUNCTION IF EXISTS knowledge_event_before_insert()")
