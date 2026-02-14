"""
Envío de push notifications vía OneSignal REST API.
Requiere ONESIGNAL_APP_ID y ONESIGNAL_REST_API_KEY.
Se envía por external_user_id (el id de usuario que usa el frontend en OneSignal.login).
"""

from __future__ import annotations

import logging

import httpx

from app.core.config import settings

ONESIGNAL_API_URL = "https://api.onesignal.com/notifications"
LOG = logging.getLogger("onesignal")


def send_push_to_user(user_id: int, title: str, body: str) -> bool:
    """
    Envía una notificación push a un usuario por su external_user_id (user.id).
    Devuelve True si se envió correctamente, False si no hay config o falla.
    """
    if not settings.ONESIGNAL_APP_ID or not settings.ONESIGNAL_REST_API_KEY:
        LOG.warning("[OneSignal] Missing ONESIGNAL_APP_ID or ONESIGNAL_REST_API_KEY; push skipped.")
        return False

    payload = {
        "app_id": settings.ONESIGNAL_APP_ID,
        "include_aliases": {"external_id": [str(user_id)]},
        "target_channel": "push",
        "contents": {"en": body},
        "headings": {"en": title} if title else None,
    }
    if not payload["headings"]:
        del payload["headings"]

    headers = {
        "Authorization": f"Key {settings.ONESIGNAL_REST_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.post(ONESIGNAL_API_URL, json=payload, headers=headers)
        if resp.status_code in (200, 201):
            return True
        LOG.warning("[OneSignal] Push failed for user %s: %s %s", user_id, resp.status_code, resp.text)
        return False
    except Exception as exc:
        LOG.exception("[OneSignal] Push failed for user %s: %s", user_id, exc)
        return False
