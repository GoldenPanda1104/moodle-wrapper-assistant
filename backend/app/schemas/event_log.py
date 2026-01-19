from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, field_validator

from app.core.event_types import EventType


class EventLogBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    event_type: str
    source: str
    payload: Optional[Dict[str, Any]] = None

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, value: str) -> str:
        if value not in EventType.values():
            raise ValueError("event_type is not a supported value")
        return value


class EventLogCreate(EventLogBase):
    pass


class EventLogRead(EventLogBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
