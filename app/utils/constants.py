from enum import StrEnum

BRAND = "☞ Ascend"
BRAND_TAGLINE = "инструмент для достижения целей"


class HabitType(StrEnum):
    CODING = "coding"
    MONEY = "money"
    WORKOUT = "workout"
    CONTENT = "content"
    STUDY = "study"
    SLEEP = "sleep"
    GAMES = "games"
    CUSTOM = "custom"


LEVELS: list[tuple[str, int, str]] = [
    ("Новичок", 0, "Только начал"),
    ("Ученик", 200, "Первые привычки"),
    ("Стажёр", 500, "Ритм появляется"),
    ("Джун", 1000, "Стабильные дни"),
    ("Разработчик", 2000, "Системная работа"),
    ("Фрилансер", 3500, "Результат за деньги"),
    ("Профи", 5500, "Высокая дисциплина"),
    ("Мастер", 8000, "Сильный контроль"),
    ("Мастер дисциплины", 12000, "Почти без срывов"),
    ("Легенда", 18000, "Максимум"),
]

XP_REWARDS: dict[str, int] = {
    "coding": 40,
    "money": 40,
    "workout": 30,
}

DEFAULT_HABITS: list[dict] = [
    {
        "name": "Направление 1",
        "habit_type": HabitType.CODING,
        "target_minutes": 1,
        "xp_reward": 40,
    },
    {
        "name": "Направление 2",
        "habit_type": HabitType.MONEY,
        "target_minutes": 1,
        "xp_reward": 40,
    },
    {
        "name": "Направление 3",
        "habit_type": HabitType.WORKOUT,
        "target_minutes": 1,
        "xp_reward": 30,
    },
]

CORE_HABIT_ORDER: list[HabitType] = [
    HabitType.CODING,
    HabitType.MONEY,
    HabitType.WORKOUT,
]
CORE_HABIT_TYPES = set(CORE_HABIT_ORDER)
