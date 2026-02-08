"""
Tests del endpoint POST /api/v1/moodle/ingest (T6).

Cubre:
- Payload válido con usuario activo: 200, aplica upserts, guarda snapshot y procesa diffs.
- user_id inexistente/inactivo o no autorizado: 4xx.
- Body malformado o no autenticado: 4xx.
"""
import pytest
from sqlalchemy.orm import Session

from app.crud import moodle as crud_moodle
from app.modules.moodle.snapshot import get_last_snapshot

from tests.conftest import make_valid_ingest_payload


def test_ingest_valid_payload_returns_200_and_applies_upserts_snapshot_diffs(
    client, db: Session, ingest_user_and_key
):
    """Payload válido con usuario activo aplica upserts, guarda snapshot y procesa diffs."""
    user, api_key = ingest_user_and_key
    payload = make_valid_ingest_payload(user.id)

    response = client.post(
        "/api/v1/moodle/ingest",
        json=payload,
        headers={"X-API-Key": api_key, "Content-Type": "application/json"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    # Upserts: el curso y el módulo existen para el usuario
    courses = crud_moodle.list_courses(db, user_id=user.id)
    assert len(courses) == 1
    assert courses[0].external_id == "c1"
    assert courses[0].name == "Curso test"

    modules = crud_moodle.list_modules(db, user_id=user.id)
    assert len(modules) == 1
    assert modules[0].external_id == "m1"
    assert modules[0].title == "Módulo 1"

    # Snapshot guardado (en disco por user_id)
    snapshot = get_last_snapshot(user.id)
    assert snapshot is not None
    assert snapshot.data.get("courses") is not None
    assert len(snapshot.data["courses"]) == 1


def test_ingest_without_api_key_returns_401(client, ingest_user_and_key):
    """Sin header X-API-Key devuelve 401."""
    user, _ = ingest_user_and_key
    payload = make_valid_ingest_payload(user.id)

    response = client.post("/api/v1/moodle/ingest", json=payload)

    assert response.status_code == 401
    assert "missing" in str(response.json().get("detail", "")).lower() or "api" in str(response.json()).lower()


def test_ingest_with_invalid_api_key_returns_401(client, ingest_user_and_key):
    """API key inválida o inexistente devuelve 401."""
    user, _ = ingest_user_and_key
    payload = make_valid_ingest_payload(user.id)

    response = client.post(
        "/api/v1/moodle/ingest",
        json=payload,
        headers={"X-API-Key": "invalid-key-not-in-db"},
    )

    assert response.status_code == 401


def test_ingest_with_valid_key_but_wrong_user_id_returns_403(client, ingest_user_and_key):
    """API key válida pero body.user_id distinto al dueño de la key devuelve 403."""
    user, api_key = ingest_user_and_key
    payload = make_valid_ingest_payload(user.id)
    payload["user_id"] = user.id + 9999  # otro user_id

    response = client.post(
        "/api/v1/moodle/ingest",
        json=payload,
        headers={"X-API-Key": api_key},
    )

    assert response.status_code == 403
    assert "another user" in str(response.json().get("detail", "")).lower()


def test_ingest_with_inactive_user_api_key_returns_401(client, db: Session, ingest_user_and_key):
    """Si el usuario dueño de la API key está inactivo, ingest devuelve 401."""
    user, api_key = ingest_user_and_key
    user.is_active = False
    db.commit()
    payload = make_valid_ingest_payload(user.id)

    response = client.post(
        "/api/v1/moodle/ingest",
        json=payload,
        headers={"X-API-Key": api_key},
    )

    assert response.status_code == 401


def test_ingest_malformed_body_missing_user_id_returns_422(client, ingest_user_and_key):
    """Body sin user_id devuelve 422."""
    _, api_key = ingest_user_and_key
    payload = make_valid_ingest_payload(1)
    del payload["user_id"]

    response = client.post(
        "/api/v1/moodle/ingest",
        json=payload,
        headers={"X-API-Key": api_key},
    )

    assert response.status_code == 422


def test_ingest_malformed_body_missing_snapshot_returns_422(client, ingest_user_and_key):
    """Body sin snapshot devuelve 422."""
    user, api_key = ingest_user_and_key
    payload = {"user_id": user.id, "diffs": []}

    response = client.post(
        "/api/v1/moodle/ingest",
        json=payload,
        headers={"X-API-Key": api_key},
    )

    assert response.status_code == 422


def test_ingest_malformed_body_invalid_json_returns_422(client, ingest_user_and_key):
    """Body que no es JSON válido o con estructura incorrecta devuelve 422."""
    _, api_key = ingest_user_and_key

    response = client.post(
        "/api/v1/moodle/ingest",
        data="not json",
        headers={"X-API-Key": api_key, "Content-Type": "application/json"},
    )

    assert response.status_code == 422
