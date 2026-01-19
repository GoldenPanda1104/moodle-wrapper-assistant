"""add course_id and completion_url to module surveys

Revision ID: 0005_add_course_completion
Revises: 0004_module_surveys
Create Date: 2026-01-19 03:15:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005_add_course_completion"
down_revision: Union[str, None] = "0004_module_surveys"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("moodle_module_surveys", sa.Column("course_id", sa.Integer(), nullable=True))
    op.add_column("moodle_module_surveys", sa.Column("completion_url", sa.String(length=1024), nullable=True))
    op.create_index(
        "ix_moodle_module_surveys_course_id",
        "moodle_module_surveys",
        ["course_id"],
        unique=False,
    )

    op.execute(
        sa.text(
            """
            UPDATE moodle_module_surveys
            SET course_id = (
                SELECT moodle_modules.course_id
                FROM moodle_modules
                WHERE moodle_modules.id = moodle_module_surveys.module_id
            )
            WHERE course_id IS NULL
            """
        )
    )

    op.alter_column("moodle_module_surveys", "course_id", nullable=False)
    op.create_foreign_key(
        "fk_moodle_module_surveys_course_id",
        "moodle_module_surveys",
        "moodle_courses",
        ["course_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_moodle_module_surveys_course_id", "moodle_module_surveys", type_="foreignkey")
    op.drop_index("ix_moodle_module_surveys_course_id", table_name="moodle_module_surveys")
    op.drop_column("moodle_module_surveys", "completion_url")
    op.drop_column("moodle_module_surveys", "course_id")
