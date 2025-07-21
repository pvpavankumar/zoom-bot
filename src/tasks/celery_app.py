
import os
from celery import Celery
from kombu import Queue

from ..core.config import settings

celery_app = Celery('zoom_interview_bot')

celery_app.conf.update(
    broker_url=settings.celery_broker_url,
    result_backend=settings.celery_result_backend,

    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=True,
    worker_pool='threads',
    worker_concurrency=4,

    task_routes={
        'src.tasks.room_tasks.create_room_bot': {'queue': 'room_management'},
        'src.tasks.room_tasks.cleanup_room_bot': {'queue': 'room_management'},
        'src.tasks.room_tasks.process_audio_task': {'queue': 'audio_processing'},
        'src.tasks.cleanup_tasks.*': {'queue': 'cleanup'},
    },

    task_always_eager=False,
    task_eager_propagates=True,
    task_ignore_result=False,
    result_expires=3600,

    task_acks_late=True,
    task_reject_on_worker_lost=True,

    worker_send_task_events=True,
    task_send_sent_event=True,

    task_default_queue='default',
    task_queues=(
        Queue('default', routing_key='default'),
        Queue('room_management', routing_key='room_management'),
        Queue('audio_processing', routing_key='audio_processing'),
        Queue('ai_processing', routing_key='ai_processing'),
        Queue('cleanup', routing_key='cleanup'),
    ),
)

celery_app.autodiscover_tasks([
    'src.tasks.room_tasks',
    'src.tasks.cleanup_tasks',
    'src.tasks.audio_tasks',
    'src.tasks.ai_tasks',
])


@celery_app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
    return 'Debug task completed'


celery_app.conf.beat_schedule = {
    'cleanup-inactive-bots': {
        'task': 'src.tasks.cleanup_tasks.cleanup_inactive_bots',
        'schedule': 300.0,
    },
    'cleanup-old-data': {
        'task': 'src.tasks.cleanup_tasks.cleanup_old_data',
        'schedule': 3600.0,
    },
}


@celery_app.task(bind=True)
def handle_task_failure(self, task_id, error, traceback):
    from ..utils.logging import get_logger

    logger = get_logger('celery.error')
    logger.error(f"Task {task_id} failed: {error}", extra={
        'task_id': task_id,
        'error': str(error),
        'traceback': traceback
    })


@celery_app.task(bind=True)
def handle_task_success(self, retval, task_id, args, kwargs):
    from ..utils.logging import get_logger

    logger = get_logger('celery.success')
    logger.info(f"Task {task_id} completed successfully", extra={
        'task_id': task_id,
        'result': str(retval)[:100]
    })


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    from ..utils.logging import get_logger

    logger = get_logger('celery.setup')
    logger.info("Celery periodic tasks configured")


if __name__ == '__main__':
    celery_app.start()
