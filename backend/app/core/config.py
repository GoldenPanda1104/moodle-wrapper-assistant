from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Suantechs Assistant"
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@db:5432/assistant"
    MOODLE_BASE_URL: str = ""
    MOODLE_USERNAME: str = ""
    MOODLE_PASSWORD: str = ""
    APP_TIMEZONE: str = "America/Panama"
    MAILERSEND_API_KEY: str = ""
    MAILERSEND_FROM_EMAIL: str = ""
    MAILERSEND_FROM_NAME: str = "Suantechs Assistant"
    MAILERSEND_TO_EMAIL: str = ""
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    SERVER_MASTER_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
