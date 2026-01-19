"""create moodle tables

Revision ID: 0002_create_moodle_tables
Revises: 0001_create_core
Create Date: 2026-01-17 19:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_create_moodle_tables"
down_revision: Union[str, None] = "0001_create_core"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "moodle_courses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_moodle_courses_id", "moodle_courses", ["id"], unique=False)
    op.create_index("ix_moodle_courses_external_id", "moodle_courses", ["external_id"], unique=True)

    op.create_table(
        "moodle_modules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("moodle_courses.id"), nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("visible", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("blocked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("block_reason", sa.String(length=255), nullable=True),
        sa.Column("has_survey", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("course_id", "external_id", name="uq_moodle_module"),
    )
    op.create_index("ix_moodle_modules_id", "moodle_modules", ["id"], unique=False)
    op.create_index("ix_moodle_modules_course_id", "moodle_modules", ["course_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_moodle_modules_course_id", table_name="moodle_modules")
    op.drop_index("ix_moodle_modules_id", table_name="moodle_modules")
    op.drop_table("moodle_modules")

    op.drop_index("ix_moodle_courses_external_id", table_name="moodle_courses")
    op.drop_index("ix_moodle_courses_id", table_name="moodle_courses")
    op.drop_table("moodle_courses")
