import asyncio
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.crud import moodle as crud_moodle
from app.db.session import get_db
from app.db.session import SessionLocal
from app.modules.moodle.complete import complete_survey as complete_moodle_survey
from app.modules.moodle.client import build_client_from_settings
from app.modules.moodle.scraper import enrich_modules_with_surveys, scrape_modules
from app.modules.moodle import pipeline as moodle_pipeline
from app.schemas.moodle_course import MoodleCourseRead
from app.schemas.moodle_module import MoodleModuleRead
from app.schemas.moodle_module_survey import MoodleModuleSurveyRead
from app.schemas.moodle_grade_item import MoodleGradeItemRead
from app.services.pipeline_stream import PipelineEvent, PipelineStreamManager

router = APIRouter()
pipeline_stream = PipelineStreamManager()


async def _refresh_course_surveys(db: Session, client, course) -> None:
    modules = await scrape_modules(client, [course.external_id])
    if not modules:
        return
    updated_modules, surveys = await enrich_modules_with_surveys(client, modules)
    course_map = {course.external_id: course}
    module_map = crud_moodle.upsert_modules(db, [module.__dict__ for module in updated_modules], course_map)
    crud_moodle.upsert_module_surveys(db, [survey.__dict__ for survey in surveys], module_map)


@router.get("/courses", response_model=list[MoodleCourseRead])
def list_courses(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    search: str | None = None,
    db: Session = Depends(get_db),
):
    return crud_moodle.list_courses(db, skip=skip, limit=limit, search=search)


@router.get("/courses/{course_id}", response_model=MoodleCourseRead)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = crud_moodle.get_course(db, course_id=course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


@router.get("/modules", response_model=list[MoodleModuleRead])
def list_modules(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    course_id: int | None = None,
    visible: bool | None = None,
    has_survey: bool | None = None,
    db: Session = Depends(get_db),
):
    return crud_moodle.list_modules(
        db,
        skip=skip,
        limit=limit,
        course_id=course_id,
        visible=visible,
        has_survey=has_survey,
    )


@router.get("/modules/{module_id}", response_model=MoodleModuleRead)
def get_module(module_id: int, db: Session = Depends(get_db)):
    module = crud_moodle.get_module(db, module_id=module_id)
    if module is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    return module


@router.get("/surveys", response_model=list[MoodleModuleSurveyRead])
def list_surveys(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    course_id: int | None = None,
    module_id: int | None = None,
    db: Session = Depends(get_db),
):
    return crud_moodle.list_module_surveys(
        db,
        skip=skip,
        limit=limit,
        course_id=course_id,
        module_id=module_id,
    )


@router.get("/surveys/{survey_id}", response_model=MoodleModuleSurveyRead)
def get_survey(survey_id: int, db: Session = Depends(get_db)):
    survey = crud_moodle.get_module_survey(db, survey_id=survey_id)
    if survey is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    return survey


@router.get("/grades", response_model=list[MoodleGradeItemRead])
def list_grade_items(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    course_id: int | None = None,
    item_type: str | None = None,
    db: Session = Depends(get_db),
):
    return crud_moodle.list_grade_items(
        db,
        skip=skip,
        limit=limit,
        course_id=course_id,
        item_type=item_type,
    )


@router.post("/surveys/complete/{survey_id}")
async def complete_survey(survey_id: int, db: Session = Depends(get_db)):
    survey = crud_moodle.get_module_survey(db, survey_id=survey_id)
    if survey is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    if not survey.completion_url:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Survey completion URL not available",
        )
    result = await complete_moodle_survey(survey.completion_url)
    if result.get("submitted") or result.get("reason") in {"completion_badge", "completion_text", "already_completed"}:
        crud_moodle.mark_survey_completed(db, survey)
    return {"detail": "Survey submission attempted", "result": result}


@router.post("/courses/{course_id}/surveys/complete-all")
async def complete_course_surveys(course_id: int, db: Session = Depends(get_db)):
    course = crud_moodle.get_course(db, course_id=course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    max_cycles = 100
    attempted: set[int] = set()
    results: list[dict] = []

    client = build_client_from_settings()
    await client.login()
    try:
        await _refresh_course_surveys(db, client, course)
        for _ in range(max_cycles):
            surveys = crud_moodle.list_module_surveys(db, course_id=course_id, limit=1000)
            pending = [
                survey
                for survey in surveys
                if survey.id not in attempted and survey.completion_url and survey.completed_at is None
            ]
            if not pending:
                break

            progress_made = False
            for survey in pending:
                attempt = await complete_moodle_survey(survey.completion_url, client=client)
                completed = attempt.get("submitted") or attempt.get("reason") in {
                    "completion_badge",
                    "completion_text",
                    "already_completed",
                }
                if completed:
                    crud_moodle.mark_survey_completed(db, survey)
                results.append(
                    {
                        "survey_id": survey.id,
                        "external_id": survey.external_id,
                        "completion_url": survey.completion_url,
                        "result": attempt,
                    }
                )
                attempted.add(survey.id)

                if completed:
                    await _refresh_course_surveys(db, client, course)
                    progress_made = True
                    break

            if not progress_made:
                break
        return {"detail": "Course surveys processed", "results": results}
    finally:
        await client.close()


@router.post("/pipeline/run")
async def run_pipeline(kind: str = "full"):
    run_id = await pipeline_stream.create_run()
    asyncio.create_task(_run_pipeline_background(run_id, kind))
    return {"run_id": run_id}


@router.get("/pipeline/stream/{run_id}")
async def stream_pipeline(run_id: str):
    try:
        queue = await pipeline_stream.subscribe(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline run not found") from exc

    async def event_stream():
        try:
            history = await pipeline_stream.history(run_id)
            for item in history:
                yield f"data: {json.dumps(item)}\n\n"
            if await pipeline_stream.is_completed(run_id):
                return
            while True:
                item = await queue.get()
                yield f"data: {json.dumps(item)}\n\n"
                if item.get("event") == "done":
                    break
        finally:
            await pipeline_stream.unsubscribe(run_id, queue)

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)


async def _run_pipeline_background(run_id: str, kind: str) -> None:
    logger = logging.getLogger("moodle")
    loop = asyncio.get_running_loop()
    handler = _PipelineLogHandler(loop, run_id)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    db = SessionLocal()
    try:
        await pipeline_stream.publish(
            run_id,
            PipelineEvent(event="status", message=f"Pipeline started ({kind}).").to_payload(),
        )
        await _run_pipeline_by_kind(db, kind)
        await pipeline_stream.mark_done(
            run_id,
            PipelineEvent(event="done", message="Pipeline completed.").to_payload(),
        )
    except Exception as exc:
        await pipeline_stream.mark_done(
            run_id,
            PipelineEvent(event="done", message=f"Pipeline failed: {exc}", level="error").to_payload(),
        )
    finally:
        logger.removeHandler(handler)
        db.close()


async def _run_pipeline_by_kind(db: Session, kind: str) -> None:
    normalized = kind.strip().lower()
    if normalized == "courses":
        await moodle_pipeline.async_run_courses_pipeline(db)
    elif normalized == "modules":
        await moodle_pipeline.async_run_modules_pipeline(db)
    elif normalized == "surveys":
        await moodle_pipeline.async_run_surveys_pipeline(db)
    elif normalized == "grades":
        await moodle_pipeline.async_run_grades_pipeline(db)
    elif normalized == "quizzes":
        await moodle_pipeline.async_run_quizzes_pipeline(db)
    else:
        await moodle_pipeline.async_run_pipeline(db)


class _PipelineLogHandler(logging.Handler):
    def __init__(self, loop: asyncio.AbstractEventLoop, run_id: str) -> None:
        super().__init__()
        self._loop = loop
        self._run_id = run_id

    def emit(self, record: logging.LogRecord) -> None:
        message = self.format(record)
        payload = PipelineEvent(
            event="log",
            message=message,
            level=record.levelname.lower(),
            ts=datetime.now(timezone.utc).isoformat(),
        ).to_payload()
        asyncio.run_coroutine_threadsafe(pipeline_stream.publish(self._run_id, payload), self._loop)
