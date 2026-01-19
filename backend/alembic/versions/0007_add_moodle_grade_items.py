"""add moodle grade items

Revision ID: 0007_add_moodle_grade_items
Revises: 0006_add_completed_at
Create Date: 2026-01-19 06:15:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007_add_moodle_grade_items"
down_revision: Union[str, None] = "0006_add_completed_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "moodle_grade_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("item_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("grade_value", sa.Float(), nullable=True),
        sa.Column("grade_display", sa.String(length=64), nullable=True),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["course_id"], ["moodle_courses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "external_id", name="uq_moodle_grade_item"),
    )
    op.create_index("ix_moodle_grade_items_id", "moodle_grade_items", ["id"], unique=False)
    op.create_index(
        "ix_moodle_grade_items_course_id",
        "moodle_grade_items",
        ["course_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_moodle_grade_items_course_id", table_name="moodle_grade_items")
    op.drop_index("ix_moodle_grade_items_id", table_name="moodle_grade_items")
    op.drop_table("moodle_grade_items")
