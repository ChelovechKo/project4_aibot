from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from ..database.types import SourceType, PostStatus


class SourceBase(BaseModel):
    type: SourceType = Field(..., description='Тип источника')
    name: str = Field(..., description='Название источника')
    url: Optional[str] = Field(None, description='URL-адрес источника')
    enabled: bool = Field(default=True, description='Включен ли источник(для парсинга)')


class SourceCreate(SourceBase):
    pass


class SourceResponse(SourceBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class SourceUpdate(BaseModel):
    type: Optional[SourceType] = None
    name: Optional[str] = None
    url: Optional[str] = None
    enabled: Optional[bool] = None


class KeywordBase(BaseModel):
    word: str = Field(..., description='Ключевое слово')


class KeywordCreate(KeywordBase):
    pass


class KeywordResponse(KeywordBase):
    id: str

    class Config:
        from_attributes = True


class NewsItemResponse(BaseModel):
    id: str
    title: str
    url: Optional[str]
    summary: str
    source: str
    published_at: datetime
    raw_text: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PostResponse(BaseModel):
    id: str
    news_id: str
    generated_text: Optional[str]
    published_at: Optional[datetime]
    status: PostStatus
    created_at: datetime
    news_item: NewsItemResponse

    class Config:
        from_attributes = True


class TelegramAuthRequest(BaseModel):
    phone: str = Field(..., description='Номер телефона в формате +7XXXXXXXXXX')
    code: Optional[str] = Field(None, description='Код подтверждения из Telegram')
    password: Optional[str] = Field(None, description='Пароль двухфакторной аутентификации')


class TelegramAuthResponse(BaseModel):
    success: bool
    message: str
    phone: Optional[str] = None
    username: Optional[str] = None
    next_step: Optional[str] = Field(None, description='Следующий шаг: code или password')