from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from app.db.base import Base


class MoodleModule(Base):
    __tablename__ = "moodle_modules"
    __table_args__ = (UniqueConstraint("course_id", "external_id", name="uq_moodle_module"),)

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("moodle_courses.id"), nullable=False, index=True)
    external_id = Column(String(64), nullable=False)
    title = Column(String(255), nullable=False)
    visible = Column(Boolean, nullable=False, default=True)
    blocked = Column(Boolean, nullable=False, default=False)
    block_reason = Column(String(255), nullable=True)
    has_survey = Column(Boolean, nullable=False, default=False)
    url = Column(String(1024), nullable=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
