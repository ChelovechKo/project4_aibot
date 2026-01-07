from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///database/aibot.database"
    REDIS_URL: str = "redis://localhost:6379/0"

    TELEGRAM_API_ID: Optional[int] = None
    TELEGRAM_API_HASH: Optional[str] = None
    TELEGRAM_SESSION_NAME: str = "aibot_session"
    TELEGRAM_CHANNEL_USERNAME: Optional[str] = None

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-40-mini"

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    PARSE_INTERVAL_MINUTES: int = 30

    DEBUG: bool = True

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()