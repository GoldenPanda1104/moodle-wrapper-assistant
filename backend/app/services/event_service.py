from sqlalchemy.orm import Session

from app.core.event_types import EventType
from app.crud import event_log as crud_event_log
from app.models.event_log import EventLog
from app.schemas.event_log import EventLogCreate


def log_event(db: Session, event_type: str, source: str, payload: dict) -> EventLog:
    if event_type not in EventType.values():
        raise ValueError("event_type is not a supported value")
    event_in = EventLogCreate(event_type=event_type, source=source, payload=payload)
    return crud_event_log.create_event_log(db, event_in=event_in)
