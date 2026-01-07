from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from uuid import uuid4

from .types import URL, TextContent#, STATUS, SOURCE_TYPE

Base = declarative_base()

class NewsItem(Base):
    __tablename__ = 'news_items'

    id: Mapped[str] = mapped_column(
        primary_key=True,
        index=True,
        default=uuid4
    )
    title: Mapped[str] = mapped_column(nullable=False)
    url: Mapped[Optional[str]] = mapped_column(nullable=False, index=True)
    summary: str = Column(Text)
    source: str = Column(String, nullable=False)
    published_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    raw_text: Mapped[Optional[str]] = Column(Text)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)

    posts = relationship("Post", back_populates="news_item")


class Post(Base):
    __tablename__ = 'posts'
    id: Mapped[str] = mapped_column(
        primary_key=True,
        index=True,
        default=uuid4
    )
    news_id: Mapped[str] = mapped_column(ForeignKey('news_items.id'))
    generated_text: Mapped[Optional[str]] = Column(Text)
    published_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    #status: STATUS = Column(Enum(STATUS), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)

    news_item = relationship("NewsItem", back_populates="posts")

class Source(Base):
    __tablename__ = 'sources'
    id: Mapped[str] = mapped_column(
        primary_key=True,
        index=True,
        default=uuid4
    )
    #type: SOURCE_TYPE
    name: str = Column(String, nullable=False)
    url: Mapped[Optional[str]] = mapped_column(nullable=False, index=True)
    enabled: bool = Column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)

class Keywords(Base):
    __tablename__ = 'keywords'
    id: Mapped[str] = mapped_column(
        primary_key=True,
        index=True,
        default=uuid4
    )
    word: str = Column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)