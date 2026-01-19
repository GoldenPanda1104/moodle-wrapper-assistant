from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict, computed_field

from app.models.task import TaskCategory, TaskPriority, TaskSource, TaskStatus


class TaskBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    title: str
    source: TaskSource
    category: TaskCategory
    status: TaskStatus = TaskStatus.pending
    priority: TaskPriority = TaskPriority.medium
    deadline: Optional[datetime] = None
    estimated_time: Optional[int] = Field(default=None, ge=1)
    blocked_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="metadata_")


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    title: Optional[str] = None
    source: Optional[TaskSource] = None
    category: Optional[TaskCategory] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    deadline: Optional[datetime] = None
    estimated_time: Optional[int] = Field(default=None, ge=1)
    blocked_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="metadata_")


class TaskRead(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @computed_field(return_type=Optional[str])
    def action_url(self) -> Optional[str]:
        return (self.metadata or {}).get("action_url")

    @computed_field(return_type=Optional[str])
    def action_label(self) -> Optional[str]:
        return (self.metadata or {}).get("action_label")
