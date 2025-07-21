
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any

from .celery_app import celery_app
from ..utils.logging import get_logger
from ..core.config import settings

logger = get_logger(__name__)


@celery_app.task(bind=True, name='src.tasks.cleanup_tasks.cleanup_inactive_bots')
def cleanup_inactive_bots(self):
    logger.info("Starting cleanup of inactive bots")

    try:
        import redis

        redis_client = redis.from_url(settings.redis_url)

        heartbeat_pattern = "bot_heartbeat:*"
        heartbeat_keys = redis_client.keys(heartbeat_pattern)

        cleaned_count = 0
        current_time = datetime.utcnow()

        for key in heartbeat_keys:
            ttl = redis_client.ttl(key)
            if ttl <= 0:
                instance_id = key.decode().split(':')[1]
                logger.warning(f"Found stale bot instance: {instance_id}")

                cleanup_key = f"bot_shutdown:{instance_id}"
                redis_client.set(cleanup_key, "true", ex=60)

                redis_client.delete(key)
                redis_client.delete(f"bot_status:{instance_id}")

                cleaned_count += 1

        logger.info(f"Cleaned up {cleaned_count} inactive bot instances")
        return {"status": "completed", "cleaned_count": cleaned_count}

    except Exception as e:
        logger.error(f"Failed to cleanup inactive bots: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True, name='src.tasks.cleanup_tasks.cleanup_old_data')
def cleanup_old_data(self):
    logger.info("Starting cleanup of old data")

    try:
        import redis
        import os

        redis_client = redis.from_url(settings.redis_url)
        cleaned_items = 0

        analysis_pattern = "conversation_analysis:*"
        analysis_keys = redis_client.keys(analysis_pattern)

        for key in analysis_keys:
            ttl = redis_client.ttl(key)
            if ttl <= 0:
                redis_client.delete(key)
                cleaned_items += 1

        audio_pattern = "audio_processing:*"
        audio_keys = redis_client.keys(audio_pattern)

        for key in audio_keys:
            ttl = redis_client.ttl(key)
            if ttl <= 0:
                redis_client.delete(key)
                cleaned_items += 1

        temp_audio_dir = "temp/audio"
        if os.path.exists(temp_audio_dir):
            cutoff_time = datetime.utcnow() - timedelta(hours=1)

            for filename in os.listdir(temp_audio_dir):
                filepath = os.path.join(temp_audio_dir, filename)
                if os.path.isfile(filepath):
                    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                    if file_time < cutoff_time:
                        os.remove(filepath)
                        cleaned_items += 1

        logger.info(f"Cleaned up {cleaned_items} old data items")
        return {"status": "completed", "cleaned_items": cleaned_items}

    except Exception as e:
        logger.error(f"Failed to cleanup old data: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True, name='src.tasks.cleanup_tasks.cleanup_failed_tasks')
def cleanup_failed_tasks(self):
    logger.info("Starting cleanup of failed tasks")

    try:
        from celery.result import AsyncResult


        import redis
        redis_client = redis.from_url(settings.redis_url)

        failed_pattern = "celery-task-meta-*"
        failed_keys = redis_client.keys(failed_pattern)

        cleaned_count = 0
        cutoff_time = datetime.utcnow() - timedelta(hours=6)

        for key in failed_keys:
            task_data = redis_client.get(key)
            if task_data:
                try:
                    import json
                    data = json.loads(task_data)
                    if data.get("status") == "FAILURE":
                        redis_client.delete(key)
                        cleaned_count += 1
                except:
                    pass

        logger.info(f"Cleaned up {cleaned_count} failed task records")
        return {"status": "completed", "cleaned_count": cleaned_count}

    except Exception as e:
        logger.error(f"Failed to cleanup failed tasks: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True, name='src.tasks.cleanup_tasks.monitor_system_resources')
def monitor_system_resources(self):
    logger.debug("Monitoring system resources")

    try:
        import psutil

        cpu_percent = psutil.cpu_percent(interval=1)

        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        disk = psutil.disk_usage('/')
        disk_percent = disk.percent

        from ..utils.logging import log_performance_metric

        log_performance_metric("cpu_usage", cpu_percent, "percent")
        log_performance_metric("memory_usage", memory_percent, "percent")
        log_performance_metric("disk_usage", disk_percent, "percent")

        alerts = []
        if cpu_percent > 80:
            alerts.append(f"High CPU usage: {cpu_percent}%")
        if memory_percent > 85:
            alerts.append(f"High memory usage: {memory_percent}%")
        if disk_percent > 90:
            alerts.append(f"High disk usage: {disk_percent}%")

        if alerts:
            logger.warning(f"Resource alerts: {', '.join(alerts)}")

        return {
            "status": "completed",
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "disk_percent": disk_percent,
            "alerts": alerts
        }

    except Exception as e:
        logger.error(f"Failed to monitor system resources: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True, name='src.tasks.cleanup_tasks.cleanup_zoom_connections')
def cleanup_zoom_connections(self):
    logger.info("Cleaning up Zoom connections")

    try:

        import redis
        redis_client = redis.from_url(settings.redis_url)

        connection_pattern = "zoom_connection:*"
        connection_keys = redis_client.keys(connection_pattern)

        cleaned_count = 0

        for key in connection_keys:
            ttl = redis_client.ttl(key)
            if ttl <= 0:
                redis_client.delete(key)
                cleaned_count += 1

        ws_pattern = "websocket:*"
        ws_keys = redis_client.keys(ws_pattern)

        for key in ws_keys:
            ttl = redis_client.ttl(key)
            if ttl <= 0:
                redis_client.delete(key)
                cleaned_count += 1

        logger.info(f"Cleaned up {cleaned_count} stale connections")
        return {"status": "completed", "cleaned_count": cleaned_count}

    except Exception as e:
        logger.error(f"Failed to cleanup Zoom connections: {e}")
        return {"status": "failed", "error": str(e)}
