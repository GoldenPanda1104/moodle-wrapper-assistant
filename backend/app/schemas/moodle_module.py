from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.schemas.moodle_course import MoodleCourseRead


class MoodleModuleRead(BaseModel):
    id: int
    course_id: int
    external_id: str
    title: str
    visible: bool
    blocked: bool
    block_reason: str | None
    has_survey: bool
    url: str | None
    last_seen_at: datetime
    created_at: datetime
    updated_at: datetime
    course: MoodleCourseRead

    model_config = ConfigDict(from_attributes=True)
