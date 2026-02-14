#!/usr/bin/env python3
"""
Prueba de envío de correo con MailerSend usando la config de .env.

Ejecutar desde la raíz del repo para que se cargue .env:

  Windows (PowerShell):
    $env:PYTHONPATH="backend"; python backend/scripts/test_email.py

  Windows (CMD):
    set PYTHONPATH=backend && python backend/scripts/test_email.py

  Linux/macOS:
    PYTHONPATH=backend python backend/scripts/test_email.py

Opcional: pasar un email como argumento para enviar ahí en lugar de MAILERSEND_TO_EMAIL.
  python backend/scripts/test_email.py otro@ejemplo.com
"""

import asyncio
import os
import sys

# Asegurar que se cargue .env de la raíz del repo
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.isfile(os.path.join(_root, ".env")):
    os.chdir(_root)
if "backend" not in sys.path and os.path.isdir(os.path.join(_root, "backend")):
    sys.path.insert(0, os.path.join(_root, "backend"))

from app.core.config import settings
from app.services.mailer import send_mailersend_email


async def main() -> None:
    to_email = (sys.argv[1] if len(sys.argv) > 1 else None) or settings.MAILERSEND_TO_EMAIL

    if not settings.MAILERSEND_API_KEY or not settings.MAILERSEND_FROM_EMAIL:
        print("ERROR: Faltan MAILERSEND_API_KEY o MAILERSEND_FROM_EMAIL en .env")
        sys.exit(1)
    if not to_email:
        print("ERROR: No hay destinatario. Define MAILERSEND_TO_EMAIL en .env o pásalo como argumento:")
        print("  python backend/scripts/test_email.py tu@email.com")
        sys.exit(1)

    subject = "Prueba de correo - Suantechs Study"
    text = "Si recibes este mensaje, el envío de correos con MailerSend está funcionando correctamente."

    print(f"Enviando a: {to_email}")
    print(f"Desde: {settings.MAILERSEND_FROM_EMAIL} ({settings.MAILERSEND_FROM_NAME})")
    try:
        await send_mailersend_email(subject, text, to_email=to_email)
        print("OK: Correo enviado. Revisa la bandeja (y spam) de", to_email)
    except Exception as e:
        print("ERROR al enviar:", e)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
