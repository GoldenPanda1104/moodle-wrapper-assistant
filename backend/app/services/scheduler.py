from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.db.session import SessionLocal
from app.modules.moodle import pipeline as moodle_pipeline
from app.services.mailer import send_mailersend_email
from app.services.moodle_digest import build_pending_summary

_scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> None:
    global _scheduler
    if _scheduler:
        return
    _scheduler = AsyncIOScheduler(timezone=settings.APP_TIMEZONE)
    _scheduler.add_job(
        _run_daily_jobs,
        CronTrigger(hour=8, minute=0),
        id="moodle_daily_jobs",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    _scheduler.start()
    logging.getLogger("scheduler").info("[Scheduler] Daily Moodle jobs scheduled at 08:00 (%s).", settings.APP_TIMEZONE)


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None


async def _run_daily_jobs() -> None:
    logger = logging.getLogger("scheduler")
    db = SessionLocal()
    try:
        await moodle_pipeline.async_run_modules_pipeline(db)
        await moodle_pipeline.async_run_grades_pipeline(db)
        await moodle_pipeline.async_run_quizzes_pipeline(db)
        subject, text = build_pending_summary(db)
        await send_mailersend_email(subject, text)
        logger.info("[Scheduler] Daily Moodle jobs completed.")
    except Exception as exc:
        logger.exception("[Scheduler] Daily Moodle jobs failed: %s", exc)
    finally:
        db.close()
