"""Endpoints de notificaciones: config OneSignal y preferencias de push/email/digest."""

from fastapi import APIRouter, Depends, status

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.api.v1.deps import get_current_user
from app.crud.notification_preferences import get_or_create_preferences, update_preferences
from app.models.user import User
from app.schemas.notification import (
    NotificationConfigResponse,
    NotificationPreferencesRead,
    NotificationPreferencesUpdate,
)

router = APIRouter()


@router.get("/config", response_model=NotificationConfigResponse)
def get_notification_config(
    current_user: User = Depends(get_current_user),
):
    """
    Configuración para el cliente: OneSignal app id y origen.
    El frontend usa esto para inicializar el SDK de push.
    """
    enabled = bool(
        settings.ONESIGNAL_APP_ID and settings.ONESIGNAL_APP_ID.strip()
    )
    return NotificationConfigResponse(
        onesignal_app_id=settings.ONESIGNAL_APP_ID or "",
        onesignal_web_origin=settings.ONESIGNAL_WEB_ORIGIN or "",
        onesignal_enabled=enabled,
    )


@router.get("/preferences", response_model=NotificationPreferencesRead)
def get_notification_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Preferencias de notificaciones del usuario (email, push, resumen diario)."""
    prefs = get_or_create_preferences(db, current_user.id)
    return NotificationPreferencesRead(
        in_app_enabled=prefs.in_app_enabled,
        email_enabled=prefs.email_enabled,
        push_enabled=prefs.push_enabled,
        daily_digest_enabled=prefs.daily_digest_enabled,
        digest_hour=prefs.digest_hour,
        timezone=prefs.timezone,
    )


@router.put("/preferences", response_model=NotificationPreferencesRead)
def update_notification_preferences(
    payload: NotificationPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Actualiza preferencias de notificaciones."""
    prefs = update_preferences(
        db,
        current_user.id,
        in_app_enabled=payload.in_app_enabled,
        email_enabled=payload.email_enabled,
        push_enabled=payload.push_enabled,
        daily_digest_enabled=payload.daily_digest_enabled,
        digest_hour=payload.digest_hour,
        timezone=payload.timezone,
    )
    return NotificationPreferencesRead(
        in_app_enabled=prefs.in_app_enabled,
        email_enabled=prefs.email_enabled,
        push_enabled=prefs.push_enabled,
        daily_digest_enabled=prefs.daily_digest_enabled,
        digest_hour=prefs.digest_hour,
        timezone=prefs.timezone,
    )


@router.get("/")
def list_notifications(
    current_user: User = Depends(get_current_user),
):
    """Lista de notificaciones in-app. Por ahora vacía (stub)."""
    return []


@router.get("/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
):
    """Cantidad de notificaciones no leídas. Por ahora 0 (stub)."""
    return {"count": 0}


@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
):
    """Marcar una notificación como leída. Stub: 200."""
    return {"id": notification_id, "read_at": None}


@router.post("/read-all")
def mark_all_read(
    current_user: User = Depends(get_current_user),
):
    """Marcar todas como leídas. Stub."""
    return {"updated": 0}
