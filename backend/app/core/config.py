from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "Moodle Wrapper"
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@db:5432/assistant"
    MOODLE_BASE_URL: str = ""
    MOODLE_USERNAME: str = ""
    MOODLE_PASSWORD: str = ""
    APP_TIMEZONE: str = "America/Panama"
    MAILERSEND_API_KEY: str = ""
    MAILERSEND_FROM_EMAIL: str = ""
    MAILERSEND_FROM_NAME: str = "Moodle Wrapper"
    MAILERSEND_TO_EMAIL: str = ""
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    SERVER_MASTER_KEY: str = ""

    class Config:
        env_file = ".env"

    @field_validator("APP_TIMEZONE", mode="before")
    @classmethod
    def normalize_app_timezone(cls, value: str) -> str:
        if value is None:
            return "America/Panama"
        normalized = str(value).strip()
        if not normalized:
            return "America/Panama"
        return normalized


settings = Settings()
