from sqlalchemy import Column, DateTime, ForeignKey, Integer, LargeBinary, Boolean
from sqlalchemy.sql import func

from app.db.base import Base


class MoodleVault(Base):
    __tablename__ = "moodle_vaults"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    credentials_ciphertext = Column(LargeBinary, nullable=False)
    credentials_nonce = Column(LargeBinary, nullable=False)
    pipeline_key_wrapped_user = Column(LargeBinary, nullable=False)
    pipeline_key_wrapped_user_nonce = Column(LargeBinary, nullable=False)
    pipeline_key_wrapped_server = Column(LargeBinary, nullable=True)
    pipeline_key_wrapped_server_nonce = Column(LargeBinary, nullable=True)
    user_kdf_salt = Column(LargeBinary, nullable=False)
    cron_enabled = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
