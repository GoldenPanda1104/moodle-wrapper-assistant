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
from app.modules.moodle.client import build_client_from_credentials
from app.modules.moodle.scraper import enrich_modules_with_surveys, scrape_modules
from app.modules.moodle import pipeline as moodle_pipeline
from app.schemas.moodle_course import MoodleCourseRead
from app.schemas.moodle_module import MoodleModuleRead
from app.schemas.moodle_module_survey import MoodleModuleSurveyRead
from app.schemas.moodle_grade_item import MoodleGradeItemRead
from app.services.pipeline_stream import PipelineEvent, PipelineStreamManager
from app.services.auth import verify_jwt_token
from app.api.v1.deps import get_current_user
from app.crud.moodle_vault import get_vault
from app.services.vault_crypto import decrypt_aes_gcm, load_server_master_key
import json as jsonlib

router = APIRouter()
pipeline_stream = PipelineStreamManager()


def _build_client_from_vault(db: Session, user_id: int):
    vault = get_vault(db, user_id)
    if not vault or not vault.pipeline_key_wrapped_server or not vault.pipeline_key_wrapped_server_nonce:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vault credentials not available")
    server_key = load_server_master_key()
    pipeline_key = decrypt_aes_gcm(
        server_key, vault.pipeline_key_wrapped_server_nonce, vault.pipeline_key_wrapped_server
    )
    creds_blob = decrypt_aes_gcm(pipeline_key, vault.credentials_nonce, vault.credentials_ciphertext)
    creds = jsonlib.loads(creds_blob.decode("utf-8"))
    return build_client_from_credentials(creds.get("username", ""), creds.get("password", ""))


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
    current_user=Depends(get_current_user),
):
    return crud_moodle.list_courses(db, user_id=current_user.id, skip=skip, limit=limit, search=search)


@router.get("/courses/{course_id}", response_model=MoodleCourseRead)
def get_course(course_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    course = crud_moodle.get_course(db, course_id=course_id, user_id=current_user.id)
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
    current_user=Depends(get_current_user),
):
    return crud_moodle.list_modules(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        course_id=course_id,
        visible=visible,
        has_survey=has_survey,
    )


@router.get("/modules/{module_id}", response_model=MoodleModuleRead)
def get_module(module_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    module = crud_moodle.get_module(db, module_id=module_id, user_id=current_user.id)
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
    current_user=Depends(get_current_user),
):
    return crud_moodle.list_module_surveys(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        course_id=course_id,
        module_id=module_id,
    )


@router.get("/surveys/{survey_id}", response_model=MoodleModuleSurveyRead)
def get_survey(survey_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    survey = crud_moodle.get_module_survey(db, survey_id=survey_id, user_id=current_user.id)
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
    current_user=Depends(get_current_user),
):
    return crud_moodle.list_grade_items(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        course_id=course_id,
        item_type=item_type,
    )


@router.post("/surveys/complete/{survey_id}")
async def complete_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    survey = crud_moodle.get_module_survey(db, survey_id=survey_id, user_id=current_user.id)
    if survey is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    if not survey.completion_url:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Survey completion URL not available",
        )
    client = _build_client_from_vault(db, current_user.id)
    await client.login()
    try:
        result = await complete_moodle_survey(survey.completion_url, client=client)
    finally:
        await client.close()
    if result.get("submitted") or result.get("reason") in {"completion_badge", "completion_text", "already_completed"}:
        crud_moodle.mark_survey_completed(db, survey)
    return {"detail": "Survey submission attempted", "result": result}


@router.post("/courses/{course_id}/surveys/complete-all")
async def complete_course_surveys(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    course = crud_moodle.get_course(db, course_id=course_id, user_id=current_user.id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    max_cycles = 100
    attempted: set[int] = set()
    results: list[dict] = []

    client = _build_client_from_vault(db, current_user.id)
    await client.login()
    try:
        await _refresh_course_surveys(db, client, course)
        for _ in range(max_cycles):
            surveys = crud_moodle.list_module_surveys(
                db, user_id=current_user.id, course_id=course_id, limit=1000
            )
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
async def run_pipeline(kind: str = "full", current_user=Depends(get_current_user)):
    run_id = await pipeline_stream.create_run()
    asyncio.create_task(_run_pipeline_background(run_id, kind, current_user.id))
    return {"run_id": run_id}


@router.get("/pipeline/stream/{run_id}")
async def stream_pipeline(run_id: str, token: str | None = None):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    verify_jwt_token(token)
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


async def _run_pipeline_background(run_id: str, kind: str, user_id: int) -> None:
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
        await _run_pipeline_by_kind(db, kind, user_id)
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


async def _run_pipeline_by_kind(db: Session, kind: str, user_id: int) -> None:
    normalized = kind.strip().lower()
    if normalized == "courses":
        await moodle_pipeline.async_run_courses_pipeline(db, user_id)
    elif normalized == "modules":
        await moodle_pipeline.async_run_modules_pipeline(db, user_id)
    elif normalized == "surveys":
        await moodle_pipeline.async_run_surveys_pipeline(db, user_id)
    elif normalized == "grades":
        await moodle_pipeline.async_run_grades_pipeline(db, user_id)
    elif normalized == "quizzes":
        await moodle_pipeline.async_run_quizzes_pipeline(db, user_id)
    else:
        await moodle_pipeline.async_run_pipeline(db, user_id)


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
