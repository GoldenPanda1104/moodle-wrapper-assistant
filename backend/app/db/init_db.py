import warnings

from app.db.base import Base
from app.db.session import engine
from app import models  # noqa: F401


def init_db() -> None:
    warnings.warn(
        "init_db is deprecated; use Alembic migrations instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    Base.metadata.create_all(bind=engine)
