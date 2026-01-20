import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.crud.moodle_vault import get_vault, upsert_vault, update_cron_status
from app.db.session import get_db
from app.schemas.vault import VaultCronToggleRequest, VaultStatus, VaultStoreRequest
from app.services.auth import verify_password
from app.services.vault_crypto import (
    decrypt_aes_gcm,
    derive_user_key,
    encrypt_aes_gcm,
    generate_salt,
    load_server_master_key,
)


router = APIRouter()


@router.get("/status", response_model=VaultStatus)
def vault_status(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    vault = get_vault(db, current_user.id)
    return VaultStatus(
        has_credentials=bool(vault),
        cron_enabled=bool(vault and vault.cron_enabled),
    )


@router.post("/store", response_model=VaultStatus)
def store_credentials(
    payload: VaultStoreRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.app_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

    user_salt = generate_salt()
    user_key = derive_user_key(payload.app_password, user_salt)
    pipeline_key = generate_salt() + generate_salt()
    pipeline_key = pipeline_key[:32]

    creds_blob = json.dumps(
        {"username": payload.moodle_username, "password": payload.moodle_password}
    ).encode("utf-8")
    creds_nonce, creds_ciphertext = encrypt_aes_gcm(pipeline_key, creds_blob)

    user_nonce, user_wrapped = encrypt_aes_gcm(user_key, pipeline_key)
    try:
        server_key = load_server_master_key()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    server_nonce, server_wrapped = encrypt_aes_gcm(server_key, pipeline_key)

    vault = upsert_vault(
        db,
        user_id=current_user.id,
        credentials_ciphertext=creds_ciphertext,
        credentials_nonce=creds_nonce,
        pipeline_key_wrapped_user=user_wrapped,
        pipeline_key_wrapped_user_nonce=user_nonce,
        pipeline_key_wrapped_server=server_wrapped,
        pipeline_key_wrapped_server_nonce=server_nonce,
        user_kdf_salt=user_salt,
        cron_enabled=True,
    )

    return VaultStatus(has_credentials=True, cron_enabled=vault.cron_enabled)


@router.post("/enable-cron", response_model=VaultStatus)
def enable_cron(
    payload: VaultCronToggleRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    vault = get_vault(db, current_user.id)
    if not vault:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vault not found")
    if not verify_password(payload.app_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

    user_key = derive_user_key(payload.app_password, vault.user_kdf_salt)
    pipeline_key = decrypt_aes_gcm(
        user_key, vault.pipeline_key_wrapped_user_nonce, vault.pipeline_key_wrapped_user
    )
    try:
        server_key = load_server_master_key()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    server_nonce, server_wrapped = encrypt_aes_gcm(server_key, pipeline_key)

    vault = update_cron_status(db, vault, True, server_wrapped, server_nonce)
    return VaultStatus(has_credentials=True, cron_enabled=vault.cron_enabled)


@router.post("/disable-cron", response_model=VaultStatus)
def disable_cron(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    vault = get_vault(db, current_user.id)
    if not vault:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vault not found")
    vault = update_cron_status(
        db, vault, False, vault.pipeline_key_wrapped_server, vault.pipeline_key_wrapped_server_nonce
    )
    return VaultStatus(has_credentials=True, cron_enabled=vault.cron_enabled)
