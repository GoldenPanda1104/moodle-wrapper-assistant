from datetime import datetime
from pydantic import BaseModel, ConfigDict


class MoodleCourseRead(BaseModel):
    id: int
    external_id: str
    name: str
    last_seen_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
