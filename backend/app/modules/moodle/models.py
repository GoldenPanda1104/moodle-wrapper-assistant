from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MoodleCourse:
    id: str
    name: str


@dataclass(frozen=True)
class MoodleModule:
    id: str
    course_id: str
    title: str
    visible: bool
    blocked: bool
    block_reason: Optional[str]
    has_survey: bool
    url: Optional[str]


@dataclass(frozen=True)
class MoodleModuleSurvey:
    id: str
    module_id: str
    course_id: str
    title: str
    url: Optional[str]
    completion_url: Optional[str]


@dataclass(frozen=True)
class MoodleGradeItem:
    id: str
    course_id: str
    title: str
    item_type: str
    grade_value: Optional[float]
    grade_display: Optional[str]
    url: Optional[str]
    available_at: Optional[str]
    due_at: Optional[str]
    submission_status: Optional[str]
    grading_status: Optional[str]
    last_submission_at: Optional[str]
    attempts_allowed: Optional[int]
    time_limit_minutes: Optional[int]
