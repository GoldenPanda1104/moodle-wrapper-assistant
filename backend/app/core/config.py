from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Suantechs Assistant"
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@db:5432/assistant"
    MOODLE_BASE_URL: str = ""
    MOODLE_USERNAME: str = ""
    MOODLE_PASSWORD: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
