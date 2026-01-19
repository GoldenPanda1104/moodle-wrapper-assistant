import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum, JSON
from sqlalchemy.sql import func

from app.db.base import Base


class TaskSource(str, enum.Enum):
    moodle = "moodle"
    platzi = "platzi"
    business = "business"
    language = "language"
    bigtech = "bigtech"


class TaskCategory(str, enum.Enum):
    study = "study"
    business = "business"
    learning = "learning"
    career = "career"
    personal = "personal"


class TaskStatus(str, enum.Enum):
    pending = "pending"
    ready = "ready"
    blocked = "blocked"
    done = "done"


class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    source = Column(Enum(TaskSource), nullable=False)
    category = Column(Enum(TaskCategory), nullable=False)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.pending)
    priority = Column(Enum(TaskPriority), nullable=False, default=TaskPriority.medium)
    deadline = Column(DateTime(timezone=True), nullable=True)
    estimated_time = Column(Integer, nullable=True)
    blocked_by = Column(String(255), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
