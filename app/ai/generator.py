import logging

from .openai_client import make_request
from ..database import NewsItem

logger = logging.getLogger(__name__)

INSTRUCTIONS = """
Вы являетесь профессиональным новостным агентом, специализирующимся на создании привлекательных и информативных новостей.
Сделай яркий, лаконичный и интересный пост на основе содержания новости для Telegram-канала, добавь emoji, call to action
"""

def generate_posts(news: NewsItem) -> str | None:
    prompt = f"""
    Новость: {news.title}
    Содержание: {news.summary}
    Источник: {news.source_id if news.source_id else 'unknown'}
    """

    logger.info(f'Генерация поста для новости: {news.id}')

    post_text = make_request(INSTRUCTIONS, prompt)

    if not post_text:
        logger.error(f'Не удалось сгенерировать пост для новости: {news.id}')
        return None
    return post_text