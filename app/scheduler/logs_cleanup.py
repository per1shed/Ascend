from __future__ import annotations

import logging
from datetime import datetime, timedelta

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


def cleanup_logs() -> None:
    """Очищает файловые логи: обрезает активные и удаляет старые."""
    settings = get_settings()
    settings.logs_dir.mkdir(parents=True, exist_ok=True)

    truncated = 0
    root = logging.getLogger()
    for handler in root.handlers:
        if not isinstance(handler, logging.FileHandler):
            continue
        handler.acquire()
        try:
            if handler.stream is not None:
                handler.stream.seek(0)
                handler.stream.truncate()
                truncated += 1
        finally:
            handler.release()

    retention = timedelta(days=settings.log_retention_days)
    now = datetime.now()
    deleted = 0
    for path in settings.logs_dir.glob("*.log*"):
        if path.name == "ascend.log":
            continue
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
        except OSError:
            continue
        if now - mtime > retention:
            path.unlink(missing_ok=True)
            deleted += 1
            logger.info("log_file_deleted", file=str(path))

    logger.info("logs_cleanup_done", truncated=truncated, deleted=deleted)
