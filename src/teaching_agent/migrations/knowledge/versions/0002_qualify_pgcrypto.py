"""Qualify pgcrypto so isolated schemas and restricted search paths verify links."""

from alembic import op

revision = "0002_qualify_pgcrypto"
down_revision = "0001_append_only_knowledge"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION knowledge_event_before_insert() RETURNS trigger AS $$
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
                IF NEW.prev IS DISTINCT FROM
                   encode(public.digest(previous.raw_line, 'sha256'), 'hex')
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


def downgrade() -> None:
    # The unqualified function is valid in the original public deployment.
    op.execute("""
        CREATE OR REPLACE FUNCTION knowledge_event_before_insert() RETURNS trigger AS $$
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
