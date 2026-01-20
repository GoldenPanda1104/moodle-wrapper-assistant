from __future__ import annotations

import asyncio
import logging

from sqlalchemy.orm import Session

from app.core.event_types import EventType
import json

from app.modules.moodle.client import build_client_from_credentials
from app.modules.moodle.diff import diff_snapshots
from app.modules.moodle.scraper import (
    enrich_modules_with_surveys,
    scrape,
    scrape_grade_items,
    scrape_modules,
)
from app.modules.moodle.snapshot import get_last_snapshot, save_snapshot
from app.modules.moodle.models import MoodleModule
from app.models.moodle_course import MoodleCourse
from app.crud import moodle as crud_moodle
from app.schemas.task import TaskCreate
from app.services.event_service import log_event
from app.crud import task as crud_task
from app.crud.moodle_vault import get_vault
from app.services.vault_crypto import decrypt_aes_gcm, load_server_master_key


def _normalize_text(value: str) -> str:
    return " ".join(value.split()).strip()


def _safe_title(title: str) -> str:
    cleaned = _normalize_text(title)
    if len(cleaned) <= 255:
        return cleaned
    return f"{cleaned[:252]}..."


def _handle_diff(db: Session, diff: dict, user_id: int) -> None:
    event_map = {
        "course_detected": EventType.MOODLE_COURSE_DETECTED,
        "module_detected": EventType.MOODLE_MODULE_DETECTED,
        "survey_detected": EventType.MOODLE_SURVEY_DETECTED,
        "blocked_detected": EventType.MOODLE_BLOCKED_DETECTED,
        "module_unlocked": EventType.MOODLE_MODULE_UNLOCKED,
    }

    event_type = event_map.get(diff["type"])
    if event_type:
        log_event(db, event_type, "moodle", diff, user_id=user_id)

    if diff["type"] == "survey_detected":
        title = f"Enviar encuesta - {diff['course']} - {diff['module']}"
        action_url = diff.get("module_url")
        metadata = {
            "course_id": diff["course_id"],
            "module_id": diff["module_id"],
        }
        if action_url:
            metadata["action_url"] = action_url
            metadata["action_label"] = "Ver encuesta"
        task_in = TaskCreate(
            title=_safe_title(title),
            source="moodle",
            category="study",
            metadata=metadata,
        )
        if crud_task.get_task_by_title_source(db, user_id, task_in.title, task_in.source) is None:
            crud_task.create_task(db, task_in=task_in, user_id=user_id)
    elif diff["type"] == "module_detected":
        title = f"Nuevo modulo disponible - {diff['course']} - {diff['module']}"
        task_in = TaskCreate(
            title=_safe_title(title),
            source="moodle",
            category="study",
            metadata={
                "course_id": diff["course_id"],
                "module_id": diff["module_id"],
            },
        )
        if crud_task.get_task_by_title_source(db, user_id, task_in.title, task_in.source) is None:
            crud_task.create_task(db, task_in=task_in, user_id=user_id)


async def async_run_pipeline(db: Session, user_id: int) -> None:
    logger = logging.getLogger("moodle")
    client = await _build_client_from_vault(db, user_id)
    await client.login()
    try:
        data = await scrape(client)
        course_map = crud_moodle.upsert_courses(db, user_id, data.get("courses", []))
        module_map = crud_moodle.upsert_modules(db, data.get("modules", []), course_map)
        crud_moodle.upsert_module_surveys(db, data.get("module_surveys", []), module_map)
        crud_moodle.upsert_grade_items(db, data.get("grade_items", []), course_map)
        previous = get_last_snapshot(user_id)
        diffs = diff_snapshots(previous.data if previous else None, data)
        save_snapshot(user_id, data)

        logger.info("[Moodle] Diffs detectados: %s", len(diffs))
        for diff in diffs:
            _handle_diff(db, diff, user_id)
    finally:
        await client.close()


async def async_run_courses_pipeline(db: Session, user_id: int) -> None:
    logger = logging.getLogger("moodle")
    client = await _build_client_from_vault(db, user_id)
    await client.login()
    try:
        courses = await client.get_courses()
        course_map = crud_moodle.upsert_courses(db, user_id, courses)
        logger.info("[Moodle] Cursos actualizados: %s", len(course_map))
    finally:
        await client.close()


async def async_run_modules_pipeline(db: Session, user_id: int) -> None:
    logger = logging.getLogger("moodle")
    client = await _build_client_from_vault(db, user_id)
    await client.login()
    try:
        course_map = await _load_or_sync_courses(db, user_id, client)
        course_ids = [course.external_id for course in course_map.values()]
        modules = await scrape_modules(client, course_ids)
        crud_moodle.upsert_modules(db, [module.__dict__ for module in modules], course_map)
        logger.info("[Moodle] Modulos actualizados: %s", len(modules))
    finally:
        await client.close()


async def async_run_surveys_pipeline(db: Session, user_id: int) -> None:
    logger = logging.getLogger("moodle")
    client = await _build_client_from_vault(db, user_id)
    await client.login()
    try:
        modules = crud_moodle.list_modules(db, user_id, limit=5000)
        module_models = [
            MoodleModule(
                id=module.external_id,
                course_id=module.course.external_id,
                title=module.title,
                visible=module.visible,
                blocked=module.blocked,
                block_reason=module.block_reason,
                has_survey=module.has_survey,
                url=module.url,
            )
            for module in modules
        ]
        updated_modules, surveys = await enrich_modules_with_surveys(client, module_models)
        course_map = await _load_or_sync_courses(db, user_id, client)
        module_map = crud_moodle.upsert_modules(
            db, [module.__dict__ for module in updated_modules], course_map
        )
        crud_moodle.upsert_module_surveys(db, [survey.__dict__ for survey in surveys], module_map)
        logger.info("[Moodle] Encuestas actualizadas: %s", len(surveys))
    finally:
        await client.close()


async def async_run_grades_pipeline(db: Session, user_id: int) -> None:
    logger = logging.getLogger("moodle")
    client = await _build_client_from_vault(db, user_id)
    await client.login()
    try:
        course_map = await _load_or_sync_courses(db, user_id, client)
        course_ids = [course.external_id for course in course_map.values()]
        grade_items = await scrape_grade_items(client, course_ids)
        crud_moodle.upsert_grade_items(db, [item.__dict__ for item in grade_items], course_map)
        logger.info("[Moodle] Calificaciones actualizadas: %s", len(grade_items))
    finally:
        await client.close()


async def async_run_quizzes_pipeline(db: Session, user_id: int) -> None:
    logger = logging.getLogger("moodle")
    client = await _build_client_from_vault(db, user_id)
    await client.login()
    try:
        course_map = await _load_or_sync_courses(db, user_id, client)
        course_ids = [course.external_id for course in course_map.values()]
        grade_items = await scrape_grade_items(client, course_ids, item_type_filter={"quiz"})
        crud_moodle.upsert_grade_items(db, [item.__dict__ for item in grade_items], course_map)
        logger.info("[Moodle] Cuestionarios actualizados: %s", len(grade_items))
    finally:
        await client.close()


def run_pipeline(db: Session, user_id: int) -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(async_run_pipeline(db, user_id))


async def _load_or_sync_courses(db: Session, user_id: int, client) -> dict[str, MoodleCourse]:
    courses = crud_moodle.list_courses(db, user_id=user_id, limit=2000)
    if courses:
        return {course.external_id: course for course in courses}
    course_rows = await client.get_courses()
    if not course_rows:
        return {}
    return crud_moodle.upsert_courses(db, user_id, course_rows)


async def _build_client_from_vault(db: Session, user_id: int):
    vault = get_vault(db, user_id)
    if not vault or not vault.pipeline_key_wrapped_server or not vault.pipeline_key_wrapped_server_nonce:
        raise RuntimeError("No cron credentials available for this user.")
    server_key = load_server_master_key()
    pipeline_key = decrypt_aes_gcm(
        server_key, vault.pipeline_key_wrapped_server_nonce, vault.pipeline_key_wrapped_server
    )
    creds_blob = decrypt_aes_gcm(pipeline_key, vault.credentials_nonce, vault.credentials_ciphertext)
    creds = json.loads(creds_blob.decode("utf-8"))
    return build_client_from_credentials(creds.get("username", ""), creds.get("password", ""))
