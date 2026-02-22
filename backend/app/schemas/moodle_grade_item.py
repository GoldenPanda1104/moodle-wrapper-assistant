from datetime import datetime
from pydantic import BaseModel, ConfigDict, computed_field

from app.schemas.moodle_course import MoodleCourseRead


class MoodleGradeItemRead(BaseModel):
    id: int
    course_id: int
    external_id: str
    item_type: str
    title: str
    grade_value: float | None
    grade_display: str | None
    url: str | None
    available_at: datetime | None
    due_at: datetime | None
    submission_status: str | None
    grading_status: str | None
    last_submission_at: datetime | None
    attempts_allowed: int | None
    time_limit_minutes: int | None
    overdue_marked_at: datetime | None
    last_seen_at: datetime
    created_at: datetime
    updated_at: datetime
    course: MoodleCourseRead

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def is_overdue(self) -> bool:
        """True si la actividad venció sin entregar (calificación 0 y no hecha)."""
        return self.overdue_marked_at is not None
