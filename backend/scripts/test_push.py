#!/usr/bin/env python3
"""
Prueba de envío de push notification con OneSignal.

Requisitos:
  1. .env con ONESIGNAL_APP_ID y ONESIGNAL_REST_API_KEY.
  2. Haber entrado al frontend con un usuario y aceptado permisos de notificaciones
     (así OneSignal asocia ese user_id al dispositivo/navegador).

Ejecutar desde la raíz del repo:

  Windows (PowerShell):
    $env:PYTHONPATH="backend"; python backend/scripts/test_push.py 1

  Linux/macOS:
    PYTHONPATH=backend python backend/scripts/test_push.py 1

El argumento es el user_id (id del usuario en la BD = external_id en OneSignal).
Si no lo sabes, consulta la tabla users en la BD o el perfil en la app.
"""

import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.isfile(os.path.join(_root, ".env")):
    os.chdir(_root)
if "backend" not in sys.path and os.path.isdir(os.path.join(_root, "backend")):
    sys.path.insert(0, os.path.join(_root, "backend"))

from app.core.config import settings
from app.services.onesignal import send_push_to_user


def main() -> None:
    if not settings.ONESIGNAL_APP_ID or not settings.ONESIGNAL_REST_API_KEY:
        print("ERROR: Faltan ONESIGNAL_APP_ID o ONESIGNAL_REST_API_KEY en .env")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Uso: python backend/scripts/test_push.py <user_id>")
        print("  user_id = id del usuario en la BD (el mismo que usa la app al hacer login en OneSignal).")
        print("  Ejemplo: python backend/scripts/test_push.py 1")
        sys.exit(1)

    try:
        user_id = int(sys.argv[1])
    except ValueError:
        print("ERROR: user_id debe ser un número (ej. 1)")
        sys.exit(1)

    title = "Prueba de push - Suantechs Study"
    body = "Si ves esta notificación, el envío de push con OneSignal funciona."

    print(f"Enviando push al user_id={user_id}...")
    ok = send_push_to_user(user_id, title, body)
    if ok:
        print("OK: Notificación enviada. Revisa el navegador o el dispositivo del usuario.")
        print("  (Si no llega: abre la app, inicia sesión y acepta notificaciones; luego vuelve a ejecutar.)")
    else:
        print("ERROR: No se pudo enviar. Revisa los logs o que el usuario tenga suscripción en OneSignal.")
        sys.exit(1)


if __name__ == "__main__":
    main()
