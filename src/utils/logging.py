
import os
import sys
import logging
from typing import Optional
from datetime import datetime
from loguru import logger as loguru_logger

from ..core.config import settings, create_log_directory


def setup_logging():
    create_log_directory()

    loguru_logger.remove()

    loguru_logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )

    loguru_logger.add(
        settings.log_file,
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="500 MB",
        retention="10 days",
        compression="zip"
    )

    class InterceptHandler(logging.Handler):
        def emit(self, record):
            try:
                level = loguru_logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            loguru_logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def get_logger(name: str):
    return loguru_logger.bind(name=name)


def log_audio_event(event_type: str, room_id: str, participant_id: Optional[str] = None, **kwargs):
    logger = get_logger("audio")

    log_data = {
        "event_type": event_type,
        "room_id": room_id,
        "timestamp": datetime.utcnow().isoformat(),
        **kwargs
    }

    if participant_id:
        log_data["participant_id"] = participant_id

    logger.info(f"Audio event: {event_type}", **log_data)


def log_ai_event(event_type: str, room_id: str, suggestion: Optional[str] = None, **kwargs):
    logger = get_logger("ai")

    log_data = {
        "event_type": event_type,
        "room_id": room_id,
        "timestamp": datetime.utcnow().isoformat(),
        **kwargs
    }

    if suggestion:
        log_data["suggestion"] = suggestion[:100] + "..." if len(suggestion) > 100 else suggestion

    logger.info(f"AI event: {event_type}", **log_data)


def log_room_event(event_type: str, room_id: str, participant_count: Optional[int] = None, **kwargs):
    logger = get_logger("room")

    log_data = {
        "event_type": event_type,
        "room_id": room_id,
        "timestamp": datetime.utcnow().isoformat(),
        **kwargs
    }

    if participant_count is not None:
        log_data["participant_count"] = participant_count

    logger.info(f"Room event: {event_type}", **log_data)


def log_performance_metric(metric_name: str, value: float, unit: str = "", **kwargs):
    logger = get_logger("performance")

    log_data = {
        "metric_name": metric_name,
        "value": value,
        "unit": unit,
        "timestamp": datetime.utcnow().isoformat(),
        **kwargs
    }

    logger.info(f"Performance metric: {metric_name}={value}{unit}", **log_data)


def log_error_with_context(error: Exception, context: dict, logger_name: str = "error"):
    logger = get_logger(logger_name)

    log_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.utcnow().isoformat(),
        **context
    }

    logger.error(f"Error occurred: {type(error).__name__}", **log_data)


class ContextualLogger:

    def __init__(self, name: str, **context):
        self.logger = get_logger(name)
        self.context = context

    def add_context(self, **kwargs):
        self.context.update(kwargs)

    def info(self, message: str, **kwargs):
        self.logger.info(message, **self.context, **kwargs)

    def warning(self, message: str, **kwargs):
        self.logger.warning(message, **self.context, **kwargs)

    def error(self, message: str, **kwargs):
        self.logger.error(message, **self.context, **kwargs)

    def debug(self, message: str, **kwargs):
        self.logger.debug(message, **self.context, **kwargs)
