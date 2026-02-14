"""Schemas para notificaciones y preferencias."""

from pydantic import BaseModel, Field


class NotificationConfigResponse(BaseModel):
    """Configuración pública para el cliente (OneSignal app id, origen)."""

    onesignal_app_id: str = ""
    onesignal_web_origin: str = ""
    onesignal_enabled: bool = False


class NotificationPreferencesRead(BaseModel):
    in_app_enabled: bool = True
    email_enabled: bool = True
    push_enabled: bool = True
    daily_digest_enabled: bool = True
    digest_hour: int = Field(ge=0, le=23, default=8)
    timezone: str | None = None

    class Config:
        from_attributes = True


class NotificationPreferencesUpdate(BaseModel):
    in_app_enabled: bool | None = None
    email_enabled: bool | None = None
    push_enabled: bool | None = None
    daily_digest_enabled: bool | None = None
    digest_hour: int | None = Field(None, ge=0, le=23)
    timezone: str | None = None
