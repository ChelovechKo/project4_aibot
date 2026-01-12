from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session

from .models import Base
from ..config import settings


def get_db_async_url():
    db_url = settings.DATABASE_URL
    if db_url.startswith('sqlite:///'):
        db_url = db_url.replace('sqlite:///', 'sqlite+aiosqlite:///')
    elif db_url.startswith('postgresql+psycopg://'):
        db_url = db_url.replace('postgresql+psycopg://', 'postgresql+asyncpg://')
    elif db_url.startswith('postgresql://'):
        db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://')
    return db_url

async_engine = create_async_engine(get_db_async_url(), echo=settings.DEBUG)

# for Celery and Alembic
sync_engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)

async_session_factory = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)  # noqa

sync_session_factory = sessionmaker(sync_engine)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


def get_db_sync() -> Generator[Session, None, None]:
    session = sync_session_factory()
    try:
        yield session
    finally:
        session.close()


async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)