import platform
from datetime import timedelta

from celery import Celery

from aibot.app.config import settings

celery_app = Celery(
    'aibot',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['aibot.app.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    queue='aibot',
    task_routes={
        'aibot.app.tasks.parse_news': {
            'queue': 'aibot',
        },
    },
    task_acks_late=True,
    task_time_limit=30,
    task_soft_time_limit=25,
    enable_utc=True,
    worker_pool='solo' if platform.system() == 'Windows' else 'prefork',
    worker_concurrency=1 if platform.system() == 'Windows' else None,
    beat_schedule={
        'parse_news': {
            'task': 'aibot.app.tasks.parse_news',
            'schedule': timedelta(minutes=settings.PARSE_INTERVAL_MINUTES),
        }
    }
)

if __name__ == '__main__':
    celery_app.start()