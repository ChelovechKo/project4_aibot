import asyncio
import logging
from datetime import datetime

from .database.models import NewsItem, Source, Post
from .database.db import get_db_sync
from .database.types import SourceType, PostStatus

from .utils import parse_site_source, parse_telegram_source
from .celery_worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.parse_news', bind=True, max_retries=3)
def parse_news(self):
    """
    Задача Celery для парсинга новостей из всех активных источников.
    Получает источники из БД, парсит их и сохраняет новости.
    """
    logger.info('Начало парсинга новостей...')

    try:
        db_gen = get_db_sync()
        session = next(db_gen)

        try:
            sources = session.query(Source).filter(Source.enabled == True).all()

            if not sources:
                logger.warning("Не найдено активных источников для парсинга")
                return {'status': 'success', 'saved': 0, 'sources_processed': 0}

            logger.info(f"Найдено активных источников: {len(sources)}")

            total_saved = 0
            for source in sources:
                # Сохраняем имя источника до обработки, чтобы избежать проблем с rollback
                source_name = source.name
                try:
                    source_type = source.type

                    if source_type == SourceType.SITE:
                        saved = parse_site_source(session, source)
                    elif source_type == SourceType.TG:
                        saved = parse_telegram_source(session, source)
                    else:
                        logger.warning(f"Неизвестный тип источника: {source_type} для '{source_name}'")
                        saved = 0

                    total_saved += saved

                except Exception as e:
                    logger.error(f"Ошибка при обработке источника '{source_name}': {e}", exc_info=True)
                    session.rollback()
                    continue

            logger.info(f'Парсинг завершен. Всего сохранено новостей: {total_saved}')

            result = {
                'status': 'success',
                'saved': total_saved,
                'sources_processed': len(sources)
            }

            return result
        except Exception as e:
            logger.error(f'Ошибка при парсинге новостей: {e}', exc_info=True)
            session.rollback()
            raise
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass

    except Exception as e:
        logger.error(f'Критическая ошибка при парсинге новостей: {e}', exc_info=True)
        raise self.retry(exc=e, countdown=60)