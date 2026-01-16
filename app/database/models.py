from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Text, ForeignKey, Enum as SQLEnum, TypeDecorator
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from uuid import uuid4

from .types import PostStatus, SourceType

def generate_uuid() -> str:
    return str(uuid4())

class SourceTypeEnum(TypeDecorator):
    """TypeDecorator для правильной работы с SourceType enum"""
    impl = String
    cache_ok = True

    def __init__(self):
        super().__init__(length=10)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, SourceType):
            return value.value
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return SourceType(value)

Base = declarative_base()

class NewsItem(Base):
    __tablename__ = 'news_items'

    id: Mapped[str] = mapped_column(
        primary_key=True,
        index=True,
        default=generate_uuid
    )
    title: Mapped[str] = mapped_column(nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String, nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String, nullable=False)
    published_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    raw_text: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)

    posts = relationship("Post", back_populates="news_item")


class Post(Base):
    __tablename__ = 'posts'
    id: Mapped[str] = mapped_column(
        primary_key=True,
        index=True,
        default=generate_uuid
    )
    news_id: Mapped[str] = mapped_column(ForeignKey('news_items.id'))
    generated_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(nullable=False)
    status: Mapped[PostStatus] = mapped_column(
        SourceTypeEnum(),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)

    news_item = relationship("NewsItem", back_populates="posts")

class Source(Base):
    __tablename__ = 'sources'
    id: Mapped[str] = mapped_column(
        primary_key=True,
        index=True,
        default=generate_uuid
    )
    type: Mapped[SourceType] = mapped_column(
        SQLEnum(SourceType, native_enum=False),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)

class Keywords(Base):
    __tablename__ = 'keywords'
    id: Mapped[str] = mapped_column(
        primary_key=True,
        index=True,
        default=generate_uuid
    )
    word: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)