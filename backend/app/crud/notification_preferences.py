"""CRUD para preferencias de notificaciones."""

from sqlalchemy.orm import Session

from app.models.notification_preferences import NotificationPreferences


def get_preferences(db: Session, user_id: int) -> NotificationPreferences | None:
    return db.query(NotificationPreferences).filter(NotificationPreferences.user_id == user_id).first()


def get_or_create_preferences(db: Session, user_id: int) -> NotificationPreferences:
    prefs = get_preferences(db, user_id)
    if prefs:
        return prefs
    prefs = NotificationPreferences(
        user_id=user_id,
        in_app_enabled=True,
        email_enabled=True,
        push_enabled=True,
        daily_digest_enabled=True,
        digest_hour=8,
    )
    db.add(prefs)
    db.commit()
    db.refresh(prefs)
    return prefs


def update_preferences(
    db: Session,
    user_id: int,
    *,
    in_app_enabled: bool | None = None,
    email_enabled: bool | None = None,
    push_enabled: bool | None = None,
    daily_digest_enabled: bool | None = None,
    digest_hour: int | None = None,
    timezone: str | None = None,
) -> NotificationPreferences:
    prefs = get_or_create_preferences(db, user_id)
    if in_app_enabled is not None:
        prefs.in_app_enabled = in_app_enabled
    if email_enabled is not None:
        prefs.email_enabled = email_enabled
    if push_enabled is not None:
        prefs.push_enabled = push_enabled
    if daily_digest_enabled is not None:
        prefs.daily_digest_enabled = daily_digest_enabled
    if digest_hour is not None:
        prefs.digest_hour = max(0, min(23, digest_hour))
    if timezone is not None:
        prefs.timezone = timezone.strip() or None
    db.commit()
    db.refresh(prefs)
    return prefs
