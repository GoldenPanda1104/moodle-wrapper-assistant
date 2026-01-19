from datetime import datetime, timedelta, timezone
from typing import Optional

from app.models.task import TaskPriority, TaskStatus


def _now_for(deadline: Optional[datetime]) -> datetime:
    if deadline is None:
        return datetime.now(timezone.utc)
    if deadline.tzinfo is None:
        return datetime.utcnow()
    return datetime.now(deadline.tzinfo)


def apply_priority_rules(status: Optional[TaskStatus], deadline: Optional[datetime]) -> Optional[TaskPriority]:
    if status == TaskStatus.blocked:
        return TaskPriority.high

    if deadline is not None:
        now = _now_for(deadline)
        if deadline - now <= timedelta(hours=24):
            return TaskPriority.critical

    return None
