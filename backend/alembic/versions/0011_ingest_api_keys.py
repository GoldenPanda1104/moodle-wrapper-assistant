"""ingest_api_keys table for scraper ingest auth

Revision ID: 0011_ingest_api_keys
Revises: 0010_add_auth_and_vault
Create Date: 2026-02-08

"""

import sqlalchemy as sa
from alembic import op

revision = "0011_ingest_api_keys"
down_revision = "0010_add_auth_and_vault"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingest_api_keys",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ingest_api_keys_user_id", "ingest_api_keys", ["user_id"], unique=True)
    op.create_index("ix_ingest_api_keys_key_hash", "ingest_api_keys", ["key_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_ingest_api_keys_key_hash", table_name="ingest_api_keys")
    op.drop_index("ix_ingest_api_keys_user_id", table_name="ingest_api_keys")
    op.drop_table("ingest_api_keys")
