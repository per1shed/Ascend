from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(..., alias="BOT_TOKEN")
    admin_id: int | None = Field(default=None, alias="ADMIN_ID")
    news_channel_id: int = Field(default=-1004327725895, alias="NEWS_CHANNEL_ID")
    news_channel_url: str = Field(
        default="https://t.me/ascednews",
        alias="NEWS_CHANNEL_URL",
    )
    database_url: str = Field(
        default="postgresql+asyncpg://ascend:ascend@localhost:5432/ascend",
        alias="DATABASE_URL",
    )
    database_url_sync: str = Field(
        default="postgresql://ascend:ascend@localhost:5432/ascend",
        alias="DATABASE_URL_SYNC",
    )
    postgres_user: str = Field(default="ascend", alias="POSTGRES_USER")
    postgres_password: str = Field(default="ascend", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="ascend", alias="POSTGRES_DB")

    timezone: str = Field(default="Europe/Moscow", alias="TIMEZONE")
    default_morning_hour: int = Field(default=8, alias="DEFAULT_MORNING_HOUR")
    default_morning_minute: int = Field(default=0, alias="DEFAULT_MORNING_MINUTE")
    default_evening_hour: int = Field(default=21, alias="DEFAULT_EVENING_HOUR")
    default_evening_minute: int = Field(default=0, alias="DEFAULT_EVENING_MINUTE")

    backup_cron_hour: int = Field(default=3, alias="BACKUP_CRON_HOUR")
    backup_retention_days: int = Field(default=14, alias="BACKUP_RETENTION_DAYS")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_retention_days: int = Field(default=7, alias="LOG_RETENTION_DAYS")
    backups_dir: Path = Field(default=BASE_DIR / "backups")
    logs_dir: Path = Field(default=BASE_DIR / "logs")


@lru_cache
def get_settings() -> Settings:
    return Settings()
