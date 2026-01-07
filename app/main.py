from fastapi import FastAPI
from contextlib import asynccontextmanager
from .database.db import init_db, async_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await async_engine.dispose()

app = FastAPI(
    title="AIBot",
    description="AIBot",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
def read_root():
    return {"Hello": "World"}
