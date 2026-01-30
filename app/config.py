from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@postgres:5432/aibot"
    REDIS_URL: str = "redis://redis:6379/0"

    TELEGRAM_API_ID: Optional[int] = 23742505
    TELEGRAM_API_HASH: Optional[str] = '3bf7aca6da2c4d1205724de09bf860b4'
    TELEGRAM_SESSION_NAME: str = "aibot_session"
    TELEGRAM_CHANNEL_USERNAME: Optional[str] = 'test_pyRush_aibot'

    OPENAI_API_KEY: Optional[str] = 'REMOVED'
    OPENAI_MODEL: str = "gpt-40-mini"

    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"

    PARSE_INTERVAL_MINUTES: int = 30
    GENERATE_INTERVAL_MINUTES: int = 30
    PUBLISH_INTERVAL_MINUTES: int = 15

    DEBUG: bool = True

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()