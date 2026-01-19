"""expand moodle course name length

Revision ID: 0003_expand_moodle_course_name
Revises: 0002_create_moodle_tables
Create Date: 2026-01-18 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0003_expand_moodle_course_name"
down_revision: Union[str, None] = "0002_create_moodle_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("moodle_courses", "name", existing_type=sa.String(length=255), type_=sa.Text())


def downgrade() -> None:
    op.alter_column("moodle_courses", "name", existing_type=sa.Text(), type_=sa.String(length=255))
