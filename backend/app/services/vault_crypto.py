import base64
import os

from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


def generate_salt() -> bytes:
    return os.urandom(16)


def derive_user_key(password: str, salt: bytes) -> bytes:
    return hash_secret_raw(
        secret=password.encode("utf-8"),
        salt=salt,
        time_cost=2,
        memory_cost=102400,
        parallelism=8,
        hash_len=32,
        type=Type.ID,
    )


def load_server_master_key() -> bytes:
    if not settings.SERVER_MASTER_KEY:
        raise ValueError("SERVER_MASTER_KEY is not configured.")
    try:
        key = base64.urlsafe_b64decode(settings.SERVER_MASTER_KEY.encode("ascii"))
    except Exception:
        key = settings.SERVER_MASTER_KEY.encode("utf-8")
    if len(key) < 32:
        raise ValueError("SERVER_MASTER_KEY must be at least 32 bytes.")
    return key[:32]


def encrypt_aes_gcm(key: bytes, plaintext: bytes) -> tuple[bytes, bytes]:
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return nonce, ciphertext


def decrypt_aes_gcm(key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)
