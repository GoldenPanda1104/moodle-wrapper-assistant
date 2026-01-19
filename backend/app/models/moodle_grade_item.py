from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class MoodleGradeItem(Base):
    __tablename__ = "moodle_grade_items"
    __table_args__ = (UniqueConstraint("course_id", "external_id", name="uq_moodle_grade_item"),)

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("moodle_courses.id"), nullable=False, index=True)
    external_id = Column(String(64), nullable=False)
    item_type = Column(String(32), nullable=False)
    title = Column(String(255), nullable=False)
    grade_value = Column(Float, nullable=True)
    grade_display = Column(String(64), nullable=True)
    url = Column(String(1024), nullable=True)
    available_at = Column(DateTime(timezone=True), nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    submission_status = Column(String(128), nullable=True)
    grading_status = Column(String(128), nullable=True)
    last_submission_at = Column(DateTime(timezone=True), nullable=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    course = relationship("MoodleCourse")
