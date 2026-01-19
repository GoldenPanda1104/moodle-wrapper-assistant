from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Iterable

from sqlalchemy.orm import Session

from app.models.moodle_course import MoodleCourse
from app.models.moodle_module import MoodleModule
from app.models.moodle_module_survey import MoodleModuleSurvey


def upsert_courses(db: Session, courses: Iterable[dict]) -> Dict[str, MoodleCourse]:
    course_list = list(courses)
    if not course_list:
        return {}

    external_ids = [course["id"] for course in course_list]
    existing = (
        db.query(MoodleCourse)
        .filter(MoodleCourse.external_id.in_(external_ids))
        .all()
    )
    existing_map = {course.external_id: course for course in existing}
    now = datetime.now(timezone.utc)

    for course in course_list:
        external_id = course["id"]
        name = course["name"]
        stored = existing_map.get(external_id)
        if stored:
            stored.name = name
            stored.last_seen_at = now
        else:
            stored = MoodleCourse(external_id=external_id, name=name, last_seen_at=now)
            db.add(stored)
            existing_map[external_id] = stored

    db.commit()
    return existing_map


def upsert_modules(
    db: Session, modules: Iterable[dict], course_map: Dict[str, MoodleCourse]
) -> Dict[tuple[str, str], MoodleModule]:
    module_list = list(modules)
    if not module_list or not course_map:
        return {}

    course_ids = {course.id for course in course_map.values()}
    existing = (
        db.query(MoodleModule)
        .filter(MoodleModule.course_id.in_(course_ids))
        .all()
    )
    existing_map = {(module.course_id, module.external_id): module for module in existing}
    now = datetime.now(timezone.utc)

    module_map: Dict[tuple[str, str], MoodleModule] = {}
    for module in module_list:
        course = course_map.get(module["course_id"])
        if not course:
            continue
        key = (course.id, module["id"])
        stored = existing_map.get(key)
        if stored:
            stored.title = module["title"]
            stored.visible = module["visible"]
            stored.blocked = module["blocked"]
            stored.block_reason = module.get("block_reason")
            stored.has_survey = module["has_survey"]
            stored.url = module.get("url")
            stored.last_seen_at = now
        else:
            stored = MoodleModule(
                course_id=course.id,
                external_id=module["id"],
                title=module["title"],
                visible=module["visible"],
                blocked=module["blocked"],
                block_reason=module.get("block_reason"),
                has_survey=module["has_survey"],
                url=module.get("url"),
                last_seen_at=now,
            )
            db.add(stored)
            existing_map[key] = stored

        module_map[(course.external_id, stored.external_id)] = stored

    db.commit()
    return module_map


def upsert_module_surveys(
    db: Session,
    surveys: Iterable[dict],
    module_map: Dict[tuple[str, str], MoodleModule],
) -> None:
    survey_list = list(surveys)
    if not survey_list or not module_map:
        return

    module_ids = {module.id for module in module_map.values()}
    existing = (
        db.query(MoodleModuleSurvey)
        .filter(MoodleModuleSurvey.module_id.in_(module_ids))
        .all()
    )
    existing_map = {(survey.module_id, survey.external_id): survey for survey in existing}
    now = datetime.now(timezone.utc)

    for survey in survey_list:
        module = module_map.get((survey["course_id"], survey["module_id"]))
        if not module:
            continue
        key = (module.id, survey["id"])
        stored = existing_map.get(key)
        if stored:
            stored.title = survey["title"]
            stored.url = survey.get("url")
            stored.last_seen_at = now
        else:
            stored = MoodleModuleSurvey(
                module_id=module.id,
                external_id=survey["id"],
                title=survey["title"],
                url=survey.get("url"),
                last_seen_at=now,
            )
            db.add(stored)

    db.commit()
