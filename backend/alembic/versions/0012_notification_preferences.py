"""notification_preferences table for push/email/digest settings

Revision ID: 0012_notification_preferences
Revises: 0011_ingest_api_keys
Create Date: 2026-02-08

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "0012_notification_preferences"
down_revision = "0011_ingest_api_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    if "notification_preferences" in insp.get_table_names():
        return
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("in_app_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("push_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("daily_digest_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("digest_hour", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("timezone", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notification_preferences_user_id", "notification_preferences", ["user_id"], unique=True)


def downgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    if "notification_preferences" not in insp.get_table_names():
        return
    op.drop_index("ix_notification_preferences_user_id", table_name="notification_preferences")
    op.drop_table("notification_preferences")
