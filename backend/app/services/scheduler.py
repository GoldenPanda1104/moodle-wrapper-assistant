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
from app.crud.moodle_vault import list_cron_enabled_vaults
from app.crud.notification_preferences import get_preferences as get_notification_preferences
from app.models.user import User
from app.services.onesignal import send_push_to_user

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
    _scheduler.add_job(
        _run_hourly_changes,
        CronTrigger(minute=0),
        id="moodle_hourly_changes",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    _scheduler.start()
    logging.getLogger("scheduler").info(
        "[Scheduler] Daily Moodle jobs at 08:00, hourly changes at :00 (%s).",
        settings.APP_TIMEZONE,
    )


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None


async def _run_hourly_changes() -> None:
    """Cada hora: sincroniza Moodle, detecta cambios y notifica por push/email si los hay."""
    logger = logging.getLogger("scheduler")
    db = SessionLocal()
    try:
        vaults = list_cron_enabled_vaults(db)
        for vault in vaults:
            user = db.query(User).filter(User.id == vault.user_id, User.is_active.is_(True)).first()
            if not user:
                continue
            try:
                diffs = await moodle_pipeline.async_run_pipeline(db, user.id)
                if not diffs or len(diffs) == 0:
                    continue
                prefs = get_notification_preferences(db, user.id)
                send_email = prefs is None or prefs.email_enabled
                send_push = prefs is None or prefs.push_enabled
                subject = "Cambios en Moodle"
                text = f"Hay {len(diffs)} novedad(es) en Moodle: nuevas tareas, calificaciones o módulos. Revisa la app."
                if send_email:
                    await send_mailersend_email(subject, text, to_email=user.email)
                if send_push:
                    send_push_to_user(user.id, subject, (text[:200] + "...") if len(text) > 200 else text)
            except Exception as user_exc:
                logger.exception(
                    "[Scheduler] Hourly changes failed for user %s: %s",
                    user.email,
                    user_exc,
                )
        logger.info("[Scheduler] Hourly changes run completed.")
    except Exception as exc:
        logger.exception("[Scheduler] Hourly changes failed: %s", exc)
    finally:
        db.close()


async def _run_daily_jobs() -> None:
    logger = logging.getLogger("scheduler")
    db = SessionLocal()
    try:
        vaults = list_cron_enabled_vaults(db)
        for vault in vaults:
            user = db.query(User).filter(User.id == vault.user_id, User.is_active.is_(True)).first()
            if not user:
                continue
            try:
                await moodle_pipeline.async_run_modules_pipeline(db, user.id)
                await moodle_pipeline.async_run_grades_pipeline(db, user.id)
                await moodle_pipeline.async_run_quizzes_pipeline(db, user.id)
                subject, text = build_pending_summary(db, user.id)
                prefs = get_notification_preferences(db, user.id)
                send_email = prefs is None or prefs.email_enabled
                send_push = prefs is not None and prefs.push_enabled and prefs.daily_digest_enabled
                if send_email:
                    await send_mailersend_email(subject, text, to_email=user.email)
                if send_push:
                    send_push_to_user(user.id, subject, (text[:200] + "...") if len(text) > 200 else text)
            except Exception as user_exc:
                logger.exception(
                    "[Scheduler] Daily Moodle jobs failed for user %s: %s",
                    user.email,
                    user_exc,
                )
        logger.info("[Scheduler] Daily Moodle jobs completed.")
    except Exception as exc:
        logger.exception("[Scheduler] Daily Moodle jobs failed: %s", exc)
    finally:
        db.close()
