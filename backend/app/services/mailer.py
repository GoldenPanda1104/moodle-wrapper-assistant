from __future__ import annotations

import logging

import httpx

from app.core.config import settings


async def send_mailersend_email(subject: str, text: str) -> None:
    if not settings.MAILERSEND_API_KEY or not settings.MAILERSEND_FROM_EMAIL or not settings.MAILERSEND_TO_EMAIL:
        logging.getLogger("mailer").warning("[MailerSend] Missing configuration; email skipped.")
        return

    payload = {
        "from": {
            "email": settings.MAILERSEND_FROM_EMAIL,
            "name": settings.MAILERSEND_FROM_NAME,
        },
        "to": [{"email": settings.MAILERSEND_TO_EMAIL}],
        "subject": subject,
        "text": text,
    }

    headers = {
        "Authorization": f"Bearer {settings.MAILERSEND_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post("https://api.mailersend.com/v1/email", json=payload, headers=headers)
        response.raise_for_status()
