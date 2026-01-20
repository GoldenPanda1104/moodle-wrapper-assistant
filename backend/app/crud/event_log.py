from sqlalchemy.orm import Session

from app.models.event_log import EventLog
from app.schemas.event_log import EventLogCreate


def create_event_log(db: Session, event_in: EventLogCreate) -> EventLog:
    event = EventLog(**event_in.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_event_logs(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    event_type: str | None = None,
    source: str | None = None,
) -> list[EventLog]:
    query = db.query(EventLog).filter(EventLog.user_id == user_id)
    if event_type:
        query = query.filter(EventLog.event_type == event_type)
    if source:
        query = query.filter(EventLog.source == source)
    return (
        query.order_by(EventLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
