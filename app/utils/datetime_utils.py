from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from app.config import get_settings


def get_tz() -> ZoneInfo:
    return ZoneInfo(get_settings().timezone)


def today() -> date:
    return datetime.now(get_tz()).date()


def now() -> datetime:
    return datetime.now(get_tz())


def next_january_1(ref: date | None = None) -> date:
    """Ближайшая дата 1 января (сегодня = 0 дней до неё)."""
    ref = ref or today()
    target = date(ref.year, 1, 1)
    if ref > target:
        target = date(ref.year + 1, 1, 1)
    return target


def days_until_january_1(ref: date | None = None) -> int:
    ref = ref or today()
    return max(0, (next_january_1(ref) - ref).days)


def is_january_1(ref: date | None = None) -> bool:
    ref = ref or today()
    return ref.month == 1 and ref.day == 1


def days_word(n: int) -> str:
    """день / дня / дней."""
    n = abs(int(n))
    n10, n100 = n % 10, n % 100
    if n10 == 1 and n100 != 11:
        return "день"
    if 2 <= n10 <= 4 and not (12 <= n100 <= 14):
        return "дня"
    return "дней"


def parse_time(value: str) -> time:
    parts = value.strip().split(":")
    if len(parts) != 2:
        raise ValueError("Формат времени: HH:MM")
    hour, minute = int(parts[0]), int(parts[1])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("Некорректное время")
    return time(hour, minute)
