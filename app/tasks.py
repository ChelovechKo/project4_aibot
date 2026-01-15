import logging

from .database.models import NewsItem, Source, Post
from .database.db import get_db_sync
from .database.types import SourceType, PostStatus

from .utils import parse_site_source, parse_telegram_source
from .celery_worker import celery_app
from aibot.app.ai.generator import generate_posts

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

            # Автоматически запускаем генерацию постов после успешного парсинга
            if total_saved > 0:
                logger.info(f'Запускаем генерацию постов для {total_saved} новых новостей')
                generate_posts_task.delay()

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

@celery_app.task(name='app.tasks.generate_posts', bind=True, max_retries=3)
def generate_posts_task(self):
    logger.info('Выполняем задачу генерации постов по новости')
    try:
        db_gen = get_db_sync()
        session = next(db_gen)

        try:
            # Находим посты со статусом NEW и получаем связанные новости
            posts = session.query(Post).filter(Post.status == PostStatus.NEW).all()
            if not posts:
                logger.info('Нет новых постов для генерации')
                return {'status': 'success', 'generated': 0}

            generated_count = 0
            for post in posts:
                try:
                    news_item = session.query(NewsItem).filter(NewsItem.id == post.news_id).first()
                    if not news_item:
                        logger.warning(f'Новость с id {post.news_id} не найдена')
                        continue

                    # TODO: filter existing news by keywords
                    post_text = generate_posts(news_item)
                    if not post_text:
                        post.status = PostStatus.FAILED
                        logger.warning(f'Не удалось сгенерировать пост для новости {news_item.id}')
                        continue

                    # Обновляем существующий пост
                    post.generated_text = post_text
                    post.status = PostStatus.GENERATED
                    generated_count += 1
                    logger.info(f'Сгенерирован пост для новости {news_item.id}')

                except Exception as e:
                    logger.error(f'Ошибка при генерации поста для новости {post.news_id}: {e}', exc_info=True)
                    post.status = PostStatus.FAILED
                    continue

            session.commit()
            logger.info(f'Генерация завершена. Сгенерировано постов: {generated_count}')

            if generated_count > 0:
                logger.info(f'Запускаем публикацию постов для {generated_count} новых новостей')
                # TODO публикация

            return {'status': 'success', 'generated': generated_count}

        except Exception as e:
            logger.error(f'Ошибка при генерации постов: {e}', exc_info=True)
            session.rollback()
            raise
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass

    except Exception as e:
        logger.error(f'Критическая ошибка при генерации постов: {e}', exc_info=True)
        raise self.retry(exc=e, countdown=60)