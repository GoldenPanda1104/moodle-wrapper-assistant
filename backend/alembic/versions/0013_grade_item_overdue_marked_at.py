"""add overdue_marked_at to moodle_grade_items

Revision ID: 0013_overdue_marked_at
Revises: 0012_notification_preferences
Create Date: 2026-02-21

"""

import sqlalchemy as sa
from alembic import op

revision = "0013_overdue_marked_at"
down_revision = "0012_notification_preferences"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "moodle_grade_items",
        sa.Column("overdue_marked_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("moodle_grade_items", "overdue_marked_at")
