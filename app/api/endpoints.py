import logging
from typing import List
import re

from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.exceptions import HTTPException
from starlette.status import HTTP_404_NOT_FOUND, HTTP_204_NO_CONTENT
from telethon import TelegramClient

from .schemas import (
    SourceResponse,
    SourceCreate,
    SourceUpdate,
    PostResponse,
    NewsItemResponse,
    TelegramAuthRequest,
    TelegramAuthResponse,
    KeywordCreate,
    KeywordResponse
)
from ..database import get_db, Source, Post, NewsItem, Keyword
from ..tasks import publish_posts_task, parse_news
from ..telegram.bot import authorize_telegram
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api', tags=['api'])


@router.get('/sources/', response_model=List[SourceResponse])
async def get_sources(
    offset: int = Query(0, ge=0, description="Смещение"),
    limit: int = Query(20, ge=1, le=100, description="Количество элементов"),
    db: AsyncSession = Depends(get_db)
):
    """Получить список источников с пагинацией"""
    result = await db.execute(select(Source).offset(offset).limit(limit))
    sources = result.scalars().all()
    return sources


@router.get('/sources/{source_id}', response_model=SourceResponse)
async def get_source(
        source_id: str = Path(..., description="UUID источника для получения"),
        db: AsyncSession = Depends(get_db)
):
    """Получить источник по его ID"""
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(HTTP_404_NOT_FOUND, 'Источник с данным id не найден')
    return source


@router.post('/sources/', status_code=201, response_model=SourceResponse)
async def create_source(
        source_data: SourceCreate = Body(..., description="Данные для создания нового источника"),
        db: AsyncSession = Depends(get_db)
):
    """Создать новый источник"""
    source = Source(**source_data.model_dump())
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


@router.put('/sources/{source_id}', response_model=SourceResponse)
async def update_source(
        source_id: str = Path(..., description="UUID источника для обновления"),
        source_data: SourceUpdate = Body(..., description="Данные для обновления источника"),
        db: AsyncSession = Depends(get_db)
):
    """Обновить данные источника по его ID"""
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(HTTP_404_NOT_FOUND, 'Источник с данным id не найден')

    source_data = source_data.model_dump(exclude_unset=True)
    for key, value in source_data.items():
        setattr(source, key, value)

    await db.commit()
    await db.refresh(source)
    return source


@router.delete('/sources/{source_id}', status_code=HTTP_204_NO_CONTENT)
async def delete_source(
        source_id: str = Path(..., description="UUID источника для удаления"),
        db: AsyncSession = Depends(get_db)
):
    """Удалить источник по его ID"""
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(HTTP_404_NOT_FOUND, 'Источник с данным id не найден')
    await db.delete(source)
    await db.commit()

@router.get('/keywords/', response_model=List[KeywordResponse])
async def get_keywords(
        offset: int = Query(0, ge=0, description="Смещение"),
        limit: int = Query(20, ge=1, le=100, description="Количество элементов"),
        db: AsyncSession = Depends(get_db)
):
    """Получить список ключевых слов с пагинацией"""
    result = await db.execute(select(Keyword).offset(offset).limit(limit))
    keywords = result.scalars().all()
    return keywords


@router.post('/keywords/', status_code=201, response_model=KeywordResponse)
async def create_keyword(
        keyword_data: KeywordCreate = Body(..., description="Данные для создания нового ключевого слова"),
        db: AsyncSession = Depends(get_db)
):
    """
    Создать новое ключевое слово.
    Ключевое слово должно быть уникальным
    """
    # Если дубль
    result = await db.execute(select(Keyword).where(Keyword.word == keyword_data.word))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail='Ключевое слово уже существует')

    keyword = Keyword(**keyword_data.model_dump())
    db.add(keyword)
    await db.commit()
    await db.refresh(keyword)
    return keyword


@router.put('/keywords/{keyword_id}', response_model=KeywordResponse)
async def update_keyword(
        keyword_id: str = Path(..., description="UUID ключевого слова для обновления"),
        keyword_data: KeywordCreate = Body(..., description="Новое ключевое слово"),
        db: AsyncSession = Depends(get_db)
):
    """
    Обновить ключевое слово.
    Полностью заменяет существующее ключевое слово новыми данными.
    Выполняется проверка на уникальность среди всех других ключевых слов.
    """
    keyword = await db.get(Keyword, keyword_id)
    if not keyword:
        raise HTTPException(
            HTTP_404_NOT_FOUND,
            'Ключевое слово с данным id не найдено'
        )

    # Проверка на дубль
    result = await db.execute(select(Keyword).where(Keyword.word == keyword_data.word, Keyword.id != keyword_id))
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail='Ключевое слово уже существует')

    keyword.word = keyword_data.word

    await db.commit()
    await db.refresh(keyword)
    return keyword


@router.delete('/keywords/{keyword_id}', status_code=HTTP_204_NO_CONTENT)
async def delete_keyword(
        keyword_id: str = Path(..., description="UUID ключевого слова для удаления"),
        db: AsyncSession = Depends(get_db)
):
    """Удалить ключевое слово по ID"""
    keyword = await db.get(Keyword, keyword_id)
    if not keyword:
        raise HTTPException(HTTP_404_NOT_FOUND, 'Ключевое слово с данным id не найдено')

    await db.delete(keyword)
    await db.commit()


@router.get('/posts/', response_model=List[PostResponse])
async def get_posts(
        offset: int = Query(0, ge=0, description="Смещение"),
        limit: int = Query(20, ge=1, le=100, description="Количество элементов"),
        db: AsyncSession = Depends(get_db)
):
    """Получить список постов с пагинацией"""
    result = await db.execute(select(Post).options(selectinload(Post.news_item)).offset(offset).limit(limit))
    posts = result.scalars().all()
    return posts


@router.get('/posts/{post_id}', response_model=PostResponse)
async def get_post(
        post_id: str = Path(..., description="UUID поста для получения"),
        db: AsyncSession = Depends(get_db)
):
    """Получить пост по его ID"""
    result = await db.execute(select(Post).options(selectinload(Post.news_item).selectinload(NewsItem.source_ref)).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(HTTP_404_NOT_FOUND, 'Пост с данным id не найден')
    return post


@router.get('/news/', response_model=List[NewsItemResponse])
async def get_news(
    offset: int = Query(0, ge=0, description="Смещение"),
    limit: int = Query(20, ge=1, le=100, description="Количество элементов"),
    db: AsyncSession = Depends(get_db)
):
    """Получить список новостей с пагинацией"""
    result = await db.execute(select(NewsItem).options(selectinload(NewsItem.source_ref)).offset(offset).limit(limit))
    news_items = result.scalars().all()
    return news_items


@router.get('/news/{news_id}', response_model=NewsItemResponse)
async def get_news_item(
    news_id: str = Path(..., description="UUID новости для получения"),
    db: AsyncSession = Depends(get_db)
):
    """Получить новость по её ID"""
    result = await db.execute(select(NewsItem).options(selectinload(NewsItem.source_ref)).where(NewsItem.id == news_id))
    news_item = result.scalar_one_or_none()
    if not news_item:
        raise HTTPException(HTTP_404_NOT_FOUND, 'Новость с данным id не найдена')
    return news_item


@router.get('/news/search/by-keywords/', response_model=List[NewsItemResponse])
async def search_news_by_keywords(
        offset: int = Query(0, ge=0, description="Смещение"),
        limit: int = Query(20, ge=1, le=100, description="Количество элементов"),
        db: AsyncSession = Depends(get_db)
):
    """Поиск новостей по ключевым словам"""
    # Получаем ключевые слова из базы
    keywords = [row[0] for row in await db.execute(select(Keyword.word))]

    if not keywords:
        raise HTTPException(status_code=400, detail="Список ключевых слов не может быть пустым")

    # Создаем условия поиска для каждого ключевого слова
    conditions = []
    for keyword in keywords:
        keyword_escaped = re.escape(keyword) # Экранируем спецсимволы для regex
        regex_pattern = f'\\m{keyword_escaped}\\M' # \m - начало слова, \M - конец слова

        conditions.append(
            or_(
                func.regexp_match(NewsItem.title, regex_pattern, 'i').isnot(None),
                func.regexp_match(NewsItem.summary, regex_pattern, 'i').isnot(None),
                func.regexp_match(NewsItem.raw_text, regex_pattern, 'i').isnot(None)
            )
        )

    search_condition = or_(*conditions)

    result = await db.execute(
        select(NewsItem)
        .options(selectinload(NewsItem.source_ref))
        .where(search_condition)
        .offset(offset)
        .limit(limit)
    )
    news_items = result.scalars().all()

    return news_items


@router.post('/publish-posts/', status_code=200)
async def publish_posts():
    """Запустить задачу публикации постов"""
    publish_posts_task.delay()
    return {'status': 'started'}


@router.post('/parse-sources/', status_code=200)
async def parse_sources():
    """Запустить задачу парсинга источников"""
    parse_news.delay()
    return {'status': 'started'}


@router.post('/telegram/authorize/', response_model=TelegramAuthResponse)
async def authorize_telegram_endpoint(
        request: TelegramAuthRequest = Body(..., description="Данные для авторизации в Telegram")
):
    """
    Авторизация в Telegram API

    Процесс авторизации:
    1. Первый запрос: отправьте только phone - получите код в Telegram
    2. Второй запрос: отправьте phone и code - авторизуетесь
    3. Если требуется 2FA: отправьте phone, code и password
    """
    result = await authorize_telegram(
        phone=request.phone,
        code=request.code,
        password=request.password
    )
    return TelegramAuthResponse(**result)


@router.get('/telegram/status/')
async def get_telegram_status():
    """Получить текущий статус авторизации в Telegram"""
    if not settings.TELEGRAM_API_ID or not settings.TELEGRAM_API_HASH:
        return {
            'authorized': False,
            'message': 'Telegram credentials not configured'
        }

    client = TelegramClient(
        settings.TELEGRAM_SESSION_NAME,
        settings.TELEGRAM_API_ID,
        settings.TELEGRAM_API_HASH
    )

    try:
        await client.connect()

        if await client.is_user_authorized():
            me = await client.get_me()
            return {
                'authorized': True,
                'phone': me.phone,
                'username': me.username,
                'first_name': me.first_name,
                'last_name': me.last_name
            }
        else:
            return {
                'authorized': False,
                'message': 'Telegram client not authorized'
            }
    except Exception as e:
        return {
            'authorized': False,
            'message': f'Error checking status: {str(e)}'
        }
    finally:
        await client.disconnect()