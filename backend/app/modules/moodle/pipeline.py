from __future__ import annotations

import asyncio
import logging

from sqlalchemy.orm import Session

from app.core.event_types import EventType
from app.modules.moodle.client import build_client_from_settings
from app.modules.moodle.diff import diff_snapshots
from app.modules.moodle.scraper import scrape
from app.modules.moodle.snapshot import get_last_snapshot, save_snapshot
from app.crud import moodle as crud_moodle
from app.schemas.task import TaskCreate
from app.services.event_service import log_event
from app.crud import task as crud_task


def _normalize_text(value: str) -> str:
    return " ".join(value.split()).strip()


def _safe_title(title: str) -> str:
    cleaned = _normalize_text(title)
    if len(cleaned) <= 255:
        return cleaned
    return f"{cleaned[:252]}..."


def _handle_diff(db: Session, diff: dict) -> None:
    event_map = {
        "course_detected": EventType.MOODLE_COURSE_DETECTED,
        "module_detected": EventType.MOODLE_MODULE_DETECTED,
        "survey_detected": EventType.MOODLE_SURVEY_DETECTED,
        "blocked_detected": EventType.MOODLE_BLOCKED_DETECTED,
        "module_unlocked": EventType.MOODLE_MODULE_UNLOCKED,
    }

    event_type = event_map.get(diff["type"])
    if event_type:
        log_event(db, event_type, "moodle", diff)

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
        crud_task.create_task(db, task_in=task_in)
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
        crud_task.create_task(db, task_in=task_in)


async def async_run_pipeline(db: Session) -> None:
    logger = logging.getLogger("moodle")
    client = build_client_from_settings()
    await client.login()
    try:
        data = await scrape(client)
        course_map = crud_moodle.upsert_courses(db, data.get("courses", []))
        module_map = crud_moodle.upsert_modules(db, data.get("modules", []), course_map)
        crud_moodle.upsert_module_surveys(db, data.get("module_surveys", []), module_map)
        crud_moodle.upsert_grade_items(db, data.get("grade_items", []), course_map)
        previous = get_last_snapshot()
        diffs = diff_snapshots(previous.data if previous else None, data)
        save_snapshot(data)

        logger.info("[Moodle] Diffs detectados: %s", len(diffs))
        for diff in diffs:
            _handle_diff(db, diff)
    finally:
        await client.close()


def run_pipeline(db: Session) -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(async_run_pipeline(db))
