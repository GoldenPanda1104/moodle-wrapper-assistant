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

    class Config:
        env_file = ".env"


settings = Settings()
