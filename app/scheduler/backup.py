from __future__ import annotations

import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


def create_backup() -> Path | None:
    settings = get_settings()
    settings.backups_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = settings.backups_dir / f"ascend_{stamp}.sql"

    env_url = settings.database_url_sync
    # postgresql://user:pass@host:port/db
    try:
        cmd = [
            "pg_dump",
            "--dbname",
            env_url,
            "--file",
            str(backup_file),
            "--no-owner",
            "--no-acl",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            logger.error("backup_failed", stderr=result.stderr)
            if backup_file.exists():
                backup_file.unlink()
            return None
        logger.info("backup_ok", file=str(backup_file))
        return backup_file
    except FileNotFoundError:
        logger.error("pg_dump_not_found")
        return None


def cleanup_old_backups() -> None:
    settings = get_settings()
    retention = timedelta(days=settings.backup_retention_days)
    now = datetime.now()
    for path in settings.backups_dir.glob("ascend_*.sql"):
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        if now - mtime > retention:
            path.unlink(missing_ok=True)
            logger.info("backup_deleted", file=str(path))


def restore_backup(backup_path: str | Path) -> bool:
    settings = get_settings()
    path = Path(backup_path)
    if not path.exists():
        logger.error("restore_file_missing", file=str(path))
        return False
    cmd = [
        "psql",
        "--dbname",
        settings.database_url_sync,
        "--file",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        logger.error("restore_failed", stderr=result.stderr)
        return False
    logger.info("restore_ok", file=str(path))
    return True
