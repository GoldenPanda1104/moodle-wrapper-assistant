from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.schemas.moodle_course import MoodleCourseRead
from app.schemas.moodle_module import MoodleModuleRead


class MoodleModuleSurveyRead(BaseModel):
    id: int
    module_id: int
    course_id: int
    external_id: str
    title: str
    url: str | None
    completion_url: str | None
    last_seen_at: datetime
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    course: MoodleCourseRead
    module: MoodleModuleRead

    model_config = ConfigDict(from_attributes=True)
