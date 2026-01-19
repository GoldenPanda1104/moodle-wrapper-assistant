from sqlalchemy.orm import Session

from app.core.event_types import EventType
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.event_service import log_event
from app.services.rules import apply_priority_rules


def get_task(db: Session, task_id: int) -> Task | None:
    return db.query(Task).filter(Task.id == task_id).first()


def list_tasks(db: Session, skip: int = 0, limit: int = 100) -> list[Task]:
    return db.query(Task).offset(skip).limit(limit).all()


def create_task(db: Session, task_in: TaskCreate) -> Task:
    data = task_in.model_dump()
    if "metadata" in data:
        data["metadata_"] = data.pop("metadata")
    rule_priority = apply_priority_rules(task_in.status, task_in.deadline)
    if rule_priority is not None:
        data["priority"] = rule_priority

    task = Task(**data)
    db.add(task)
    db.commit()
    db.refresh(task)
    log_event(
        db,
        EventType.TASK_CREATED,
        "core",
        {"task_id": task.id, "title": task.title},
    )
    return task


def update_task(db: Session, task: Task, task_in: TaskUpdate) -> Task:
    previous_status = task.status
    data = task_in.model_dump(exclude_unset=True)
    if "metadata" in data:
        data["metadata_"] = data.pop("metadata")
    status = data.get("status", task.status)
    deadline = data.get("deadline", task.deadline)
    rule_priority = apply_priority_rules(status, deadline)
    if rule_priority is not None:
        data["priority"] = rule_priority

    for field, value in data.items():
        setattr(task, field, value)

    db.add(task)
    db.commit()
    db.refresh(task)
    if previous_status != TaskStatus.done and task.status == TaskStatus.done:
        log_event(
            db,
            EventType.TASK_COMPLETED,
            "core",
            {"task_id": task.id, "title": task.title},
        )
    return task


def delete_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()
