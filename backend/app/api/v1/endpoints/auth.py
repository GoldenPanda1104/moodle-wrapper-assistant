from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.crud.user import create_user, get_user_by_email
from app.crud.refresh_token import create_refresh_token, delete_refresh_token, get_refresh_token
from app.db.session import get_db
from app.schemas.auth import RefreshRequest, TokenPair, UserCreate, UserLogin, UserOut
from app.services.auth import (
    create_access_token,
    create_refresh_token as create_refresh_token_value,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.core.config import settings


router = APIRouter()


@router.post("/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    password_hash = hash_password(payload.password)
    user = create_user(db, payload.email, password_hash)
    return user


@router.post("/login", response_model=TokenPair)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email)
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token_value()
    refresh_hash = hash_refresh_token(refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    create_refresh_token(db, user.id, refresh_hash, expires_at)
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    refresh_hash = hash_refresh_token(payload.refresh_token)
    token = get_refresh_token(db, refresh_hash)
    if not token or token.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    access_token = create_access_token(str(token.user_id))
    new_refresh_token = create_refresh_token_value()
    new_hash = hash_refresh_token(new_refresh_token)
    token.token_hash = new_hash
    token.expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.commit()
    return TokenPair(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/logout")
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    refresh_hash = hash_refresh_token(payload.refresh_token)
    token = get_refresh_token(db, refresh_hash)
    if token:
        delete_refresh_token(db, token)
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(current_user=Depends(get_current_user)):
    return current_user
