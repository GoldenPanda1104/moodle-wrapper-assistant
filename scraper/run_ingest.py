#!/usr/bin/env python3
"""
Script de ingest Moodle (T4): obtiene datos del sitio Moodle y los envía al backend
mediante POST a /api/v1/moodle/ingest. Reutilizable desde la imagen Docker del scraper
o en local con PYTHONPATH=backend.

- Lee credenciales Moodle, USER_ID, INGEST_URL e INGEST_API_KEY desde env.
- Ejecuta adapter + snapshot + diffs (sin depender de BD en el scraper).
- POST con reintentos (2–3 intentos con backoff) según spec.
"""
import asyncio
import logging
import os
import sys
import time

import httpx

# En Docker: código en /app/app; en local: PYTHONPATH=backend o añadir backend aquí.
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.abspath(__file__).startswith("/app"):
    sys.path.insert(0, "/app")
elif os.path.isdir(os.path.join(_root, "backend")):
    sys.path.insert(0, os.path.join(_root, "backend"))
if os.environ.get("PYTHONPATH"):
    for p in os.environ["PYTHONPATH"].split(os.pathsep):
        if p and p not in sys.path:
            sys.path.insert(0, p)

from app.modules.moodle.adapters import get_adapter
from app.modules.moodle.diff import diff_snapshots
from app.modules.moodle.fetch import _fetch_modules, _merge_survey_flags
from app.modules.moodle.snapshot import get_last_snapshot, save_snapshot

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("scraper")


def _get_env(key: str, alt: str | None = None) -> str:
    value = os.environ.get(key) or (os.environ.get(alt) if alt else None)
    if not value or not value.strip():
        raise SystemExit(f"Falta variable de entorno: {key} (o {alt})")
    return value.strip()


async def run_ingest() -> None:
    base_url = _get_env("MOODLE_BASE_URL")
    username = _get_env("MOODLE_USERNAME")
    password = _get_env("MOODLE_PASSWORD")
    user_id = int(_get_env("USER_ID"))
    ingest_url = _get_env("INGEST_URL").rstrip("/")
    api_key = _get_env("INGEST_API_KEY", "API_KEY")

    adapter = get_adapter({
        "base_url": base_url,
        "username": username,
        "password": password,
    })
    await adapter.login()
    try:
        courses = await adapter.get_courses()
        modules = await _fetch_modules(adapter, courses)
        surveys = await adapter.get_surveys()
        modules = _merge_survey_flags(modules, surveys)
        grade_items = await adapter.get_grades()

        previous = get_last_snapshot(user_id)
        snapshot = {
            "courses": [c.__dict__ for c in courses],
            "modules": [m.__dict__ for m in modules],
            "module_surveys": [s.__dict__ for s in surveys],
            "grade_items": [i.__dict__ for i in grade_items],
        }
        diffs = diff_snapshots(previous.data if previous else None, snapshot)

        logger.info("Snapshot: %s cursos, %s módulos, %s diffs", len(courses), len(modules), len(diffs))

        payload = {"user_id": user_id, "snapshot": snapshot, "diffs": diffs}
        url = f"{ingest_url}/api/v1/moodle/ingest"
        headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    save_snapshot(user_id, snapshot)
                    logger.info("Ingest OK")
                    return
                logger.warning("Ingest attempt %s: %s %s", attempt, resp.status_code, resp.text)
                if 400 <= resp.status_code < 500:
                    raise SystemExit(f"Backend rechazó el payload: {resp.status_code} {resp.text}")
            except httpx.HTTPError as e:
                logger.warning("Ingest attempt %s failed: %s", attempt, e)
            if attempt < max_attempts:
                time.sleep(2**attempt)
        raise SystemExit("Ingest falló después de reintentos")
    finally:
        await adapter.close()


def main() -> None:
    asyncio.run(run_ingest())


if __name__ == "__main__":
    main()
