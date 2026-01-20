from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.moodle.models import (
    MoodleCourse,
    MoodleGradeItem,
    MoodleModule,
    MoodleModuleSurvey,
)


class MoodleAdapter(ABC):
    @abstractmethod
    async def login(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_courses(self) -> list[MoodleCourse]:
        raise NotImplementedError

    @abstractmethod
    async def get_modules(self, course_id: str) -> list[MoodleModule]:
        raise NotImplementedError

    @abstractmethod
    async def get_grades(self) -> list[MoodleGradeItem]:
        raise NotImplementedError

    @abstractmethod
    async def get_quizzes(self) -> list[MoodleGradeItem]:
        raise NotImplementedError

    @abstractmethod
    async def get_surveys(self) -> list[MoodleModuleSurvey]:
        raise NotImplementedError

    @abstractmethod
    async def complete_survey(self, completion_url: str) -> dict:
        raise NotImplementedError
