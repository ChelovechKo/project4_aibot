from enum import Enum
from datetime import datetime

from sqlalchemy.sql.annotation import Annotated
from uuid import uuid4
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.orm import Mapped
from sqlalchemy.testing.schema import mapped_column


class PostStatus(str, Enum):
    NEW = 'new'
    GENERATED = 'generated'
    PUBLISHED = 'published'
    FAILED = 'failed'

class SourceType(str, Enum):
    SITE = 'site'
    TG  = 'tg'

ID = Annotated[Mapped[int], mapped_column(
       primary_key=True,
       index=True,
       default=uuid4
    )
]
URL = Annotated[str, Column(String, nullable=False, index=True)]
TextContent = Annotated[str, Column(Text)]
TimeStamp = Annotated[datetime, Column(DateTime, nullable=False, default=datetime.now)]
#STATUS = Annotated[PostStatus, Column(Enum(PostStatus), nullable=False)]
#SOURCE_TYPE = Annotated[SourceType, Column(Enum(SourceType), nullable=False)]