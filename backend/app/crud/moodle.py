from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Iterable

from app.models.moodle_course import MoodleCourse
from app.models.moodle_module import MoodleModule
from app.models.moodle_module_survey import MoodleModuleSurvey
from app.models.moodle_grade_item import MoodleGradeItem
from sqlalchemy.orm import Session, joinedload


def get_course(db: Session, course_id: int, user_id: int) -> MoodleCourse | None:
    return (
        db.query(MoodleCourse)
        .filter(MoodleCourse.id == course_id, MoodleCourse.user_id == user_id)
        .first()
    )


def list_courses(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
) -> list[MoodleCourse]:
    query = db.query(MoodleCourse).filter(MoodleCourse.user_id == user_id)
    if search:
        query = query.filter(MoodleCourse.name.ilike(f"%{search}%"))
    return query.order_by(MoodleCourse.name.asc()).offset(skip).limit(limit).all()


def get_module(db: Session, module_id: int, user_id: int) -> MoodleModule | None:
    return (
        db.query(MoodleModule)
        .options(joinedload(MoodleModule.course))
        .filter(MoodleModule.id == module_id, MoodleModule.course.has(user_id=user_id))
        .first()
    )


def list_modules(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    course_id: int | None = None,
    visible: bool | None = None,
    has_survey: bool | None = None,
) -> list[MoodleModule]:
    query = (
        db.query(MoodleModule)
        .options(joinedload(MoodleModule.course))
        .join(MoodleModule.course)
        .filter(MoodleCourse.user_id == user_id)
    )
    if course_id is not None:
        query = query.filter(MoodleModule.course_id == course_id)
    if visible is not None:
        query = query.filter(MoodleModule.visible == visible)
    if has_survey is not None:
        query = query.filter(MoodleModule.has_survey == has_survey)
    return (
        query.order_by(MoodleModule.course_id.asc(), MoodleModule.external_id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_module_survey(db: Session, survey_id: int, user_id: int) -> MoodleModuleSurvey | None:
    return (
        db.query(MoodleModuleSurvey)
        .options(joinedload(MoodleModuleSurvey.course), joinedload(MoodleModuleSurvey.module))
        .join(MoodleModuleSurvey.course)
        .filter(MoodleModuleSurvey.id == survey_id, MoodleCourse.user_id == user_id)
        .first()
    )


def list_module_surveys(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    course_id: int | None = None,
    module_id: int | None = None,
) -> list[MoodleModuleSurvey]:
    query = (
        db.query(MoodleModuleSurvey)
        .options(
            joinedload(MoodleModuleSurvey.course),
            joinedload(MoodleModuleSurvey.module),
        )
        .join(MoodleModuleSurvey.course)
        .filter(MoodleCourse.user_id == user_id)
    )
    if course_id is not None:
        query = query.filter(MoodleModuleSurvey.course_id == course_id)
    if module_id is not None:
        query = query.filter(MoodleModuleSurvey.module_id == module_id)
    return (
        query.order_by(
            MoodleModuleSurvey.completed_at.isnot(None).asc(),
            MoodleModuleSurvey.course_id.asc(),
            MoodleModuleSurvey.external_id.asc(),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def list_grade_items(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    course_id: int | None = None,
    item_type: str | None = None,
) -> list[MoodleGradeItem]:
    query = (
        db.query(MoodleGradeItem)
        .options(joinedload(MoodleGradeItem.course))
        .join(MoodleGradeItem.course)
        .filter(MoodleCourse.user_id == user_id)
    )
    if course_id is not None:
        query = query.filter(MoodleGradeItem.course_id == course_id)
    if item_type is not None:
        query = query.filter(MoodleGradeItem.item_type == item_type)
    return (
        query.order_by(
            MoodleGradeItem.course_id.asc(),
            MoodleGradeItem.external_id.asc(),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def mark_survey_completed(db: Session, survey: MoodleModuleSurvey) -> MoodleModuleSurvey:
    now = datetime.now(timezone.utc)
    survey.completed_at = now
    db.add(survey)
    db.commit()
    db.refresh(survey)
    return survey


def upsert_courses(db: Session, user_id: int, courses: Iterable[dict]) -> Dict[str, MoodleCourse]:
    course_list = list(courses)
    if not course_list:
        return {}

    external_ids = [course["id"] for course in course_list]
    existing = (
        db.query(MoodleCourse)
        .filter(MoodleCourse.user_id == user_id, MoodleCourse.external_id.in_(external_ids))
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
            stored = MoodleCourse(user_id=user_id, external_id=external_id, name=name, last_seen_at=now)
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
            stored.completion_url = survey.get("completion_url")
            stored.course_id = module.course_id
            stored.last_seen_at = now
        else:
            stored = MoodleModuleSurvey(
                module_id=module.id,
                course_id=module.course_id,
                external_id=survey["id"],
                title=survey["title"],
                url=survey.get("url"),
                completion_url=survey.get("completion_url"),
                last_seen_at=now,
            )
            db.add(stored)

    db.commit()


def upsert_grade_items(
    db: Session,
    items: Iterable[dict],
    course_map: Dict[str, MoodleCourse],
) -> None:
    item_list = list(items)
    if not item_list or not course_map:
        return

    course_ids = {course.id for course in course_map.values()}
    existing = (
        db.query(MoodleGradeItem)
        .filter(MoodleGradeItem.course_id.in_(course_ids))
        .all()
    )
    existing_map = {(item.course_id, item.external_id): item for item in existing}
    now = datetime.now(timezone.utc)

    for item in item_list:
        course = course_map.get(item["course_id"])
        if not course:
            continue
        key = (course.id, item["id"])
        stored = existing_map.get(key)
        available_at = _coerce_datetime(item.get("available_at"))
        due_at = _coerce_datetime(item.get("due_at"))
        last_submission_at = _coerce_datetime(item.get("last_submission_at"))
        attempts_allowed = _coerce_int(item.get("attempts_allowed"))
        time_limit_minutes = _coerce_int(item.get("time_limit_minutes"))
        if stored:
            stored.title = item["title"]
            stored.item_type = item["item_type"]
            stored.grade_value = item.get("grade_value")
            stored.grade_display = item.get("grade_display")
            stored.url = item.get("url")
            stored.available_at = available_at
            stored.due_at = due_at
            stored.submission_status = item.get("submission_status")
            stored.grading_status = item.get("grading_status")
            stored.last_submission_at = last_submission_at
            stored.attempts_allowed = attempts_allowed
            stored.time_limit_minutes = time_limit_minutes
            stored.last_seen_at = now
        else:
            stored = MoodleGradeItem(
                course_id=course.id,
                external_id=item["id"],
                item_type=item["item_type"],
                title=item["title"],
                grade_value=item.get("grade_value"),
                grade_display=item.get("grade_display"),
                url=item.get("url"),
                available_at=available_at,
                due_at=due_at,
                submission_status=item.get("submission_status"),
                grading_status=item.get("grading_status"),
                last_submission_at=last_submission_at,
                attempts_allowed=attempts_allowed,
                time_limit_minutes=time_limit_minutes,
                last_seen_at=now,
            )
            db.add(stored)

    db.commit()


def _coerce_datetime(value: str | datetime | None) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _coerce_int(value: int | str | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except ValueError:
        return None
