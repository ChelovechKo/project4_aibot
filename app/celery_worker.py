import platform
from datetime import timedelta

from celery import Celery
from .config import settings

celery_app = Celery(
    'aibot',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.tasks']
)

@celery_app.on_after_configure.connect
def setup_initial_tasks(sender, **kwargs):
    # чтоб не ждать 30 минут и сделать сразу первый запуск
    sender.send_task('app.tasks.parse_news', queue='parsing')
    sender.send_task('app.tasks.generate_posts', queue='generation')

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    task_default_queue='default',
    task_routes={
        'app.tasks.parse_news': {
            'queue': 'parsing',
        },
        'app.tasks.generate_posts': {
            'queue': 'generation',
        },
    },
    task_acks_late=True,
    task_time_limit=300,  # 5 минут для генерации
    task_soft_time_limit=240,  # 4 минуты мягкий лимит
    enable_utc=True,
    timezone = 'Europe/Athens',
    worker_pool='solo' if platform.system() == 'Windows' else 'prefork',
    worker_concurrency=1 if platform.system() == 'Windows' else None,
    beat_schedule={
        'parse_news': {
            'task': 'app.tasks.parse_news',
            'schedule': timedelta(minutes=settings.PARSE_INTERVAL_MINUTES)
        },
        'generate_posts': {
            'task': 'app.tasks.generate_posts',
            'schedule': timedelta(minutes=settings.GENERATE_INTERVAL_MINUTES)
        }
    }
)

if __name__ == '__main__':
    celery_app.start()