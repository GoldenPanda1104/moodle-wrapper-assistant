"""add completed_at to module surveys

Revision ID: 0006_add_completed_at
Revises: 0005_add_course_completion
Create Date: 2026-01-19 04:20:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006_add_completed_at"
down_revision: Union[str, None] = "0005_add_course_completion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "moodle_module_surveys",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("moodle_module_surveys", "completed_at")
