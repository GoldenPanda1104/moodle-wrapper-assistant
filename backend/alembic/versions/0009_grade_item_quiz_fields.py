"""add grade item quiz fields

Revision ID: 0009_add_grade_item_quiz_fields
Revises: 0008_grade_item_status_fields
Create Date: 2026-01-19 06:55:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009_add_grade_item_quiz_fields"
down_revision: Union[str, None] = "0008_grade_item_status_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "moodle_grade_items",
        sa.Column("attempts_allowed", sa.Integer(), nullable=True),
    )
    op.add_column(
        "moodle_grade_items",
        sa.Column("time_limit_minutes", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("moodle_grade_items", "time_limit_minutes")
    op.drop_column("moodle_grade_items", "attempts_allowed")
