from enum import Enum

class PostStatus(str, Enum):
    NEW = 'new'
    GENERATED = 'generated'
    PUBLISHED = 'published'
    FAILED = 'failed'

class SourceType(str, Enum):
    SITE = 'site'
    TG  = 'tg'