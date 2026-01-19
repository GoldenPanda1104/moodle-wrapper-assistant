"""create tasks and event logs

Revision ID: 0001_create_core
Revises: 
Create Date: 2026-01-16 15:36:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0001_create_core"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE tasksource AS ENUM ('moodle','platzi','business','language','bigtech'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
    )
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE taskcategory AS ENUM ('study','business','learning','career','personal'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
    )
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE taskstatus AS ENUM ('pending','ready','blocked','done'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
    )
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE taskpriority AS ENUM ('low','medium','high','critical'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column(
            "source",
            postgresql.ENUM(
                "moodle",
                "platzi",
                "business",
                "language",
                "bigtech",
                name="tasksource",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "category",
            postgresql.ENUM(
                "study",
                "business",
                "learning",
                "career",
                "personal",
                name="taskcategory",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "ready",
                "blocked",
                "done",
                name="taskstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "priority",
            postgresql.ENUM(
                "low",
                "medium",
                "high",
                "critical",
                name="taskpriority",
                create_type=False,
            ),
            nullable=False,
            server_default="medium",
        ),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estimated_time", sa.Integer(), nullable=True),
        sa.Column("blocked_by", sa.String(length=255), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_tasks_id", "tasks", ["id"], unique=False)

    op.create_table(
        "event_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_event_logs_id", "event_logs", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_event_logs_id", table_name="event_logs")
    op.drop_table("event_logs")

    op.drop_index("ix_tasks_id", table_name="tasks")
    op.drop_table("tasks")

    op.execute("DROP TYPE IF EXISTS taskpriority")
    op.execute("DROP TYPE IF EXISTS taskstatus")
    op.execute("DROP TYPE IF EXISTS taskcategory")
    op.execute("DROP TYPE IF EXISTS tasksource")
