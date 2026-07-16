# Ascend

Telegram-бот для ежедневного фокуса до 1 января.

Один экран: сколько дней осталось и три отметки — программирование, заработок, тренировка. Плюс график активности в стиле Apple Health.

## Что умеет

- Счётчик дней до 1 января
- Отметки за день (можно снять повторным нажатием)
- График активности по неделям (пн–вс)
- Выходной день без отметок
- Утреннее и вечернее напоминание
- Автобэкап PostgreSQL

## Команды

| Команда | Назначение |
|---------|------------|
| `/start` `/today` | Главный экран |
| `/stats` | График активности |
| `/rest` | Выходной |
| `/settings` | Время утра и вечера |
| `/help` | Краткая справка |

## Стек

Python 3.12 · aiogram 3 · PostgreSQL · SQLAlchemy 2 · Alembic · APScheduler · Pillow · Docker · pytest

## Быстрый старт (Docker)

1. Создайте `.env` в корне проекта:

```env
BOT_TOKEN=токен_от_BotFather
POSTGRES_USER=ascend
POSTGRES_PASSWORD=ascend
POSTGRES_DB=ascend
DATABASE_URL=postgresql+asyncpg://ascend:ascend@db:5432/ascend
DATABASE_URL_SYNC=postgresql://ascend:ascend@db:5432/ascend
TIMEZONE=Europe/Moscow
```

2. Запустите:

```bash
docker compose up -d --build
```

3. Напишите боту `/start` в Telegram.

Полезные команды:

```bash
docker compose logs -f bot   # логи
docker compose restart bot   # перезапуск
docker compose down          # остановка
```

## Локальный запуск

Нужны Python 3.12+ и PostgreSQL.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

В `.env` укажите `localhost` вместо `db` в URL базы, затем:

```bash
alembic upgrade head
python -m app.main
```

Тесты:

```bash
pytest
```

## Структура проекта

```
app/
  handlers/      # Telegram: today, stats, rest, settings, evening
  services/      # привычки, график, XP, серия, отчёты
  models/        # ORM
  repositories/  # доступ к БД
  scheduler/     # утро / вечер / backup
  keyboards/     # inline-кнопки
  config/        # настройки из .env
alembic/         # миграции
scripts/         # backup / restore
tests/
```

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен Telegram-бота |
| `DATABASE_URL` | Async URL (asyncpg) |
| `DATABASE_URL_SYNC` | Sync URL для Alembic |
| `POSTGRES_USER` / `PASSWORD` / `DB` | Учётные данные PostgreSQL |
| `TIMEZONE` | Часовой пояс (по умолчанию `Europe/Moscow`) |
| `DEFAULT_MORNING_HOUR` / `MINUTE` | Утро по умолчанию (8:00) |
| `DEFAULT_EVENING_HOUR` / `MINUTE` | Вечер по умолчанию (21:00) |
| `BACKUP_CRON_HOUR` | Час ежедневного бэкапа (3) |
| `BACKUP_RETENTION_DAYS` | Сколько дней хранить дампы (14) |
