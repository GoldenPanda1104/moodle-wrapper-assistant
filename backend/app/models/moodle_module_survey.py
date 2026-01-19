from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class MoodleModuleSurvey(Base):
    __tablename__ = "moodle_module_surveys"
    __table_args__ = (UniqueConstraint("module_id", "external_id", name="uq_moodle_module_survey"),)

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("moodle_modules.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("moodle_courses.id"), nullable=False, index=True)
    external_id = Column(String(64), nullable=False)
    title = Column(String(255), nullable=False)
    url = Column(String(1024), nullable=True)
    completion_url = Column(String(1024), nullable=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    module = relationship("MoodleModule")
    course = relationship("MoodleCourse")
