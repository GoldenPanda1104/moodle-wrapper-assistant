"""add auth tables and vault

Revision ID: 0010_add_auth_and_vault
Revises: 0009_grade_item_quiz_fields
Create Date: 2026-01-20 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "0010_add_auth_and_vault"
down_revision = "0009_add_grade_item_quiz_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"], unique=False)

    op.create_table(
        "moodle_vaults",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("credentials_ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("credentials_nonce", sa.LargeBinary(), nullable=False),
        sa.Column("pipeline_key_wrapped_user", sa.LargeBinary(), nullable=False),
        sa.Column("pipeline_key_wrapped_user_nonce", sa.LargeBinary(), nullable=False),
        sa.Column("pipeline_key_wrapped_server", sa.LargeBinary(), nullable=True),
        sa.Column("pipeline_key_wrapped_server_nonce", sa.LargeBinary(), nullable=True),
        sa.Column("user_kdf_salt", sa.LargeBinary(), nullable=False),
        sa.Column("cron_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_moodle_vault_user"),
    )

    op.add_column("tasks", sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True))
    op.create_index("ix_tasks_user_id", "tasks", ["user_id"], unique=False)

    op.add_column(
        "event_logs",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
    )
    op.create_index("ix_event_logs_user_id", "event_logs", ["user_id"], unique=False)

    op.add_column(
        "moodle_courses",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
    )
    op.create_index("ix_moodle_courses_user_id", "moodle_courses", ["user_id"], unique=False)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = 'ix_moodle_courses_external_id'
            ) THEN
                EXECUTE 'DROP INDEX ix_moodle_courses_external_id';
            END IF;
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'moodle_courses_external_id_key'
            ) THEN
                EXECUTE 'ALTER TABLE moodle_courses DROP CONSTRAINT moodle_courses_external_id_key';
            END IF;
        END$$;
        """
    )
    op.create_unique_constraint("uq_moodle_courses_user_external", "moodle_courses", ["user_id", "external_id"])


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uq_moodle_courses_user_external'
            ) THEN
                EXECUTE 'ALTER TABLE moodle_courses DROP CONSTRAINT uq_moodle_courses_user_external';
            END IF;
        END$$;
        """
    )
    op.create_index("ix_moodle_courses_external_id", "moodle_courses", ["external_id"], unique=True)
    op.drop_index("ix_moodle_courses_user_id", table_name="moodle_courses")
    op.drop_column("moodle_courses", "user_id")

    op.drop_index("ix_event_logs_user_id", table_name="event_logs")
    op.drop_column("event_logs", "user_id")

    op.drop_index("ix_tasks_user_id", table_name="tasks")
    op.drop_column("tasks", "user_id")

    op.drop_table("moodle_vaults")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
