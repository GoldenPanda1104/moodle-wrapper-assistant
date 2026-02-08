"""
Fixtures para tests del API. Requiere DATABASE_URL (o la por defecto del proyecto).
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.crud.user import create_user as crud_create_user
from app.crud.ingest_api_key import create_ingest_api_key
from app.services.auth import hash_password


@pytest.fixture(scope="function")
def db() -> Session:
    """Sesión de BD para setup y assertions. Se cierra al salir."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client() -> TestClient:
    """Cliente HTTP contra la app FastAPI (sin override de BD)."""
    return TestClient(app)


@pytest.fixture(scope="function")
def ingest_user_and_key(db: Session):
    """
    Crea un usuario activo y su API key de ingest. Devuelve (user, api_key).
    Email único por test para evitar colisiones.
    """
    email = f"ingest_test_{uuid.uuid4().hex}@test.local"
    password_hash = hash_password("test-pass-change-me")
    user = crud_create_user(db, email=email, password_hash=password_hash)
    api_key = create_ingest_api_key(db, user.id)
    return user, api_key


def make_valid_ingest_payload(user_id: int):
    """Payload mínimo válido según docs/moodle-ingest-spec.md."""
    return {
        "user_id": user_id,
        "snapshot": {
            "courses": [{"id": "c1", "name": "Curso test"}],
            "modules": [
                {
                    "id": "m1",
                    "course_id": "c1",
                    "title": "Módulo 1",
                    "visible": True,
                    "blocked": False,
                    "block_reason": None,
                    "has_survey": False,
                    "url": None,
                }
            ],
            "module_surveys": [],
            "grade_items": [],
        },
        "diffs": [
            {
                "type": "module_detected",
                "course_id": "c1",
                "course": "Curso test",
                "module_id": "m1",
                "module": "Módulo 1",
                "module_url": None,
            }
        ],
    }
