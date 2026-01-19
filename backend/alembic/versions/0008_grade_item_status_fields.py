"""add grade item status fields

Revision ID: 0008_grade_item_status_fields
Revises: 0007_add_moodle_grade_items
Create Date: 2026-01-19 06:35:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008_grade_item_status_fields"
down_revision: Union[str, None] = "0007_add_moodle_grade_items"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "moodle_grade_items",
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "moodle_grade_items",
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "moodle_grade_items",
        sa.Column("submission_status", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "moodle_grade_items",
        sa.Column("grading_status", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "moodle_grade_items",
        sa.Column("last_submission_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("moodle_grade_items", "last_submission_at")
    op.drop_column("moodle_grade_items", "grading_status")
    op.drop_column("moodle_grade_items", "submission_status")
    op.drop_column("moodle_grade_items", "due_at")
    op.drop_column("moodle_grade_items", "available_at")
