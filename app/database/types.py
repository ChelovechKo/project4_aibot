from enum import Enum


class PostStatus(str, Enum):
    """Статусы поста"""
    NEW = "new"
    GENERATED = "generated"
    PUBLISHED = "published"
    FAILED = "failed"


class SourceType(str, Enum):
    """Типы источников новостей"""
    SITE = "site"
    TG = "tg"