"""CRUD para API keys de ingest (scraper → backend)."""

import secrets

from sqlalchemy.orm import Session

from app.models.ingest_api_key import IngestApiKey
from app.models.user import User


def _hash_key(plain_key: str) -> str:
    import hashlib
    return hashlib.sha256(plain_key.encode("utf-8")).hexdigest()


def create_ingest_api_key(db: Session, user_id: int) -> str:
    """
    Crea o reemplaza la API key de ingest del usuario.
    Devuelve la clave en claro (solo se muestra una vez al generarla).
    """
    plain_key = secrets.token_urlsafe(32)
    key_hash = _hash_key(plain_key)

    db.query(IngestApiKey).filter(IngestApiKey.user_id == user_id).delete()
    row = IngestApiKey(user_id=user_id, key_hash=key_hash)
    db.add(row)
    db.commit()
    return plain_key


def get_user_by_api_key(db: Session, plain_key: str) -> User | None:
    """
    Si la API key es válida, devuelve el usuario asociado (y activo); si no, None.
    """
    if not plain_key or not plain_key.strip():
        return None
    key_hash = _hash_key(plain_key.strip())
    row = db.query(IngestApiKey).filter(IngestApiKey.key_hash == key_hash).first()
    if not row:
        return None
    from app.crud.user import get_user
    user = get_user(db, row.user_id)
    return user if (user and user.is_active) else None
