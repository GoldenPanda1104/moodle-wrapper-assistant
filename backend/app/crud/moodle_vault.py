from sqlalchemy.orm import Session

from app.models.moodle_vault import MoodleVault


def get_vault(db: Session, user_id: int) -> MoodleVault | None:
    return db.query(MoodleVault).filter(MoodleVault.user_id == user_id).first()


def upsert_vault(
    db: Session,
    user_id: int,
    credentials_ciphertext: bytes,
    credentials_nonce: bytes,
    pipeline_key_wrapped_user: bytes,
    pipeline_key_wrapped_user_nonce: bytes,
    pipeline_key_wrapped_server: bytes | None,
    pipeline_key_wrapped_server_nonce: bytes | None,
    user_kdf_salt: bytes,
    cron_enabled: bool,
) -> MoodleVault:
    vault = get_vault(db, user_id)
    if vault:
        vault.credentials_ciphertext = credentials_ciphertext
        vault.credentials_nonce = credentials_nonce
        vault.pipeline_key_wrapped_user = pipeline_key_wrapped_user
        vault.pipeline_key_wrapped_user_nonce = pipeline_key_wrapped_user_nonce
        vault.pipeline_key_wrapped_server = pipeline_key_wrapped_server
        vault.pipeline_key_wrapped_server_nonce = pipeline_key_wrapped_server_nonce
        vault.user_kdf_salt = user_kdf_salt
        vault.cron_enabled = cron_enabled
    else:
        vault = MoodleVault(
            user_id=user_id,
            credentials_ciphertext=credentials_ciphertext,
            credentials_nonce=credentials_nonce,
            pipeline_key_wrapped_user=pipeline_key_wrapped_user,
            pipeline_key_wrapped_user_nonce=pipeline_key_wrapped_user_nonce,
            pipeline_key_wrapped_server=pipeline_key_wrapped_server,
            pipeline_key_wrapped_server_nonce=pipeline_key_wrapped_server_nonce,
            user_kdf_salt=user_kdf_salt,
            cron_enabled=cron_enabled,
        )
        db.add(vault)
    db.commit()
    db.refresh(vault)
    return vault


def update_cron_status(
    db: Session,
    vault: MoodleVault,
    enabled: bool,
    pipeline_key_wrapped_server: bytes | None,
    pipeline_key_wrapped_server_nonce: bytes | None,
) -> MoodleVault:
    vault.cron_enabled = enabled
    vault.pipeline_key_wrapped_server = pipeline_key_wrapped_server
    vault.pipeline_key_wrapped_server_nonce = pipeline_key_wrapped_server_nonce
    db.commit()
    db.refresh(vault)
    return vault


def list_cron_enabled_vaults(db: Session) -> list[MoodleVault]:
    return db.query(MoodleVault).filter(MoodleVault.cron_enabled.is_(True)).all()
