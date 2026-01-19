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
