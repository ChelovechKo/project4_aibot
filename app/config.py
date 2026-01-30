from typing import Optional
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@postgres:5432/aibot")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    TELEGRAM_API_ID: Optional[int] = os.getenv("TELEGRAM_API_ID", 23742505)
    TELEGRAM_API_HASH: Optional[str] = os.getenv("TELEGRAM_API_HASH", "")
    TELEGRAM_SESSION_NAME: str = os.getenv("TELEGRAM_SESSION_NAME", "aibot_session")
    TELEGRAM_CHANNEL_USERNAME: Optional[str] = os.getenv("TELEGRAM_CHANNEL_USERNAME", "")

    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-40-mini"

    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

    PARSE_INTERVAL_MINUTES: int = 30
    GENERATE_INTERVAL_MINUTES: int = 30
    PUBLISH_INTERVAL_MINUTES: int = 5

    DEBUG: bool = True

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


settings = Settings()
