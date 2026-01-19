"""create moodle module surveys

Revision ID: 0004_module_surveys
Revises: 0003_expand_moodle_course_name
Create Date: 2026-01-19 00:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0004_module_surveys"
down_revision: Union[str, None] = "0003_expand_moodle_course_name"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "moodle_module_surveys",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("module_id", sa.Integer(), sa.ForeignKey("moodle_modules.id"), nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("module_id", "external_id", name="uq_moodle_module_survey"),
    )
    op.create_index("ix_moodle_module_surveys_id", "moodle_module_surveys", ["id"], unique=False)
    op.create_index(
        "ix_moodle_module_surveys_module_id", "moodle_module_surveys", ["module_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_moodle_module_surveys_module_id", table_name="moodle_module_surveys")
    op.drop_index("ix_moodle_module_surveys_id", table_name="moodle_module_surveys")
    op.drop_table("moodle_module_surveys")
