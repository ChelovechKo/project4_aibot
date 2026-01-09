import logging

from aibot.celery_worker import celery_app
from aibot.app.database.db import get_db_sync
from aibot.app.database.models import Source
from aibot.app.utils import parse_site_source, parse_telegram_source

logger = logging.getLogger(__name__)


@celery_app.task(name='aibot.app.tasks.parse_news', bind=True, max_retries=3)
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
                try:
                    source_type = getattr(source, 'type', 'site')

                    if source_type == 'site':
                        saved = parse_site_source(session, source)
                    elif source_type == 'tg':
                        saved = parse_telegram_source(session, source)
                    else:
                        logger.warning(f"Неизвестный тип источника: {source_type} для '{source.name}'")
                        saved = 0

                    total_saved += saved

                except Exception as e:
                    logger.error(f"Ошибка при обработке источника '{source.name}': {e}", exc_info=True)
                    continue

            logger.info(f'Парсинг завершен. Всего сохранено новостей: {total_saved}')

            return {
                'status': 'success',
                'saved': total_saved,
                'sources_processed': len(sources)
            }
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass

    except Exception as e:
        logger.error(f'Критическая ошибка при парсинге новостей: {e}', exc_info=True)
        raise self.retry(exc=e, countdown=60)