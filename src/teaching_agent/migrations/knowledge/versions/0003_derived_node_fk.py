"""Remove FK privilege coupling from the insert-only derived node projection."""

from alembic import op

revision = "0003_derived_node_fk"
down_revision = "0002_qualify_pgcrypto"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("nodes_created_event_id_fkey", "nodes", type_="foreignkey")


def downgrade() -> None:
    op.create_foreign_key(
        "nodes_created_event_id_fkey", "nodes", "events", ["created_event_id"], ["id"]
    )
