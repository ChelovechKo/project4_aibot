from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database.db import init_db, async_engine
from fixtures import create_fixtures_sync
import asyncio
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Инициализация БД...")
    await init_db()

    logger.info("Запуск фикстур...")
    await asyncio.to_thread(create_fixtures_sync)

    logger.info("Приложение готово к работе")
    yield

    logger.info("Закрытие соединений с БД...")
    await async_engine.dispose()

app = FastAPI(
    title="AIBot",
    description="AIBot",
    version="0.0.1",
    lifespan=lifespan
)

@app.get("/")
def read_root():
    return {"Hello": "World"}