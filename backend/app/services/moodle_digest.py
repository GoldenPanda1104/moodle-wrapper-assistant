from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.crud import moodle as crud_moodle
from app.core.config import settings


def build_pending_summary(db: Session, user_id: int) -> tuple[str, str]:
    try:
        tz = ZoneInfo(settings.APP_TIMEZONE)
    except Exception:
        tz = ZoneInfo("UTC")
    now = datetime.now(tz)
    cutoff = now + timedelta(days=7)

    surveys = crud_moodle.list_module_surveys(db, user_id=user_id, limit=5000)
    pending_surveys = [survey for survey in surveys if survey.completed_at is None]

    assignments = crud_moodle.list_grade_items(
        db, user_id=user_id, item_type="assignment", limit=5000
    )
    pending_assignments = []
    for item in assignments:
        status = (item.submission_status or "").lower()
        not_submitted = "enviado" not in status
        due_at = item.due_at
        within_window = due_at is None or due_at <= cutoff
        if not_submitted and within_window:
            pending_assignments.append(item)

    quizzes = crud_moodle.list_grade_items(db, user_id=user_id, item_type="quiz", limit=5000)
    pending_quizzes = []
    for item in quizzes:
        due_at = item.due_at
        within_window = due_at is None or due_at <= cutoff
        if item.grade_value is None and within_window:
            pending_quizzes.append(item)

    subject = "Resumen diario Moodle - Pendientes"
    lines = []
    lines.append(f"Resumen diario ({settings.APP_TIMEZONE}): {now.isoformat()}")
    lines.append("")
    lines.append(f"Encuestas pendientes: {len(pending_surveys)}")
    for survey in pending_surveys[:10]:
        course = survey.course.name if survey.course else "Curso"
        lines.append(f"- {survey.title} ({course})")
    if len(pending_surveys) > 10:
        lines.append(f"... y {len(pending_surveys) - 10} mas")
    lines.append("")
    lines.append(f"Tareas por entregar (7 dias): {len(pending_assignments)}")
    for item in pending_assignments[:10]:
        course = item.course.name if item.course else "Curso"
        due = item.due_at.isoformat() if item.due_at else "Sin fecha"
        lines.append(f"- {item.title} ({course}) - cierre {due}")
    if len(pending_assignments) > 10:
        lines.append(f"... y {len(pending_assignments) - 10} mas")
    lines.append("")
    lines.append(f"Cuestionarios por realizar (7 dias): {len(pending_quizzes)}")
    for item in pending_quizzes[:10]:
        course = item.course.name if item.course else "Curso"
        due = item.due_at.isoformat() if item.due_at else "Sin fecha"
        lines.append(f"- {item.title} ({course}) - cierre {due}")
    if len(pending_quizzes) > 10:
        lines.append(f"... y {len(pending_quizzes) - 10} mas")

    return subject, "\n".join(lines)
