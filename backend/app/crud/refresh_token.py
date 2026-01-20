from datetime import datetime

from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


def create_refresh_token(db: Session, user_id: int, token_hash: str, expires_at: datetime) -> RefreshToken:
    token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def get_refresh_token(db: Session, token_hash: str) -> RefreshToken | None:
    return db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()


def delete_refresh_token(db: Session, token: RefreshToken) -> None:
    db.delete(token)
    db.commit()
