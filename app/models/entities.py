from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    level_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("levels.id", ondelete="RESTRICT"), nullable=False, default=1
    )
    plan_start_date: Mapped[date] = mapped_column(Date, nullable=False, default=func.current_date())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    level: Mapped["Level"] = relationship("Level", back_populates="users", lazy="joined")
    goals: Mapped[list["Goal"]] = relationship(
        "Goal", back_populates="user", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="user", cascade="all, delete-orphan"
    )
    habits: Mapped[list["Habit"]] = relationship(
        "Habit", back_populates="user", cascade="all, delete-orphan"
    )
    settings: Mapped["UserSettings"] = relationship(
        "UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    streak: Mapped["Streak"] = relationship(
        "Streak", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    finances: Mapped[list["Finance"]] = relationship(
        "Finance", back_populates="user", cascade="all, delete-orphan"
    )
    workouts: Mapped[list["Workout"]] = relationship(
        "Workout", back_populates="user", cascade="all, delete-orphan"
    )
    weight_logs: Mapped[list["WeightLog"]] = relationship(
        "WeightLog", back_populates="user", cascade="all, delete-orphan"
    )
    body_progress: Mapped[list["BodyProgress"]] = relationship(
        "BodyProgress", back_populates="user", cascade="all, delete-orphan"
    )
    achievements: Mapped[list["UserAchievement"]] = relationship(
        "UserAchievement", back_populates="user", cascade="all, delete-orphan"
    )
    rest_days: Mapped[list["RestDay"]] = relationship(
        "RestDay", back_populates="user", cascade="all, delete-orphan"
    )
    daily_reports: Mapped[list["DailyReport"]] = relationship(
        "DailyReport", back_populates="user", cascade="all, delete-orphan"
    )
    weekly_reports: Mapped[list["WeeklyReport"]] = relationship(
        "WeeklyReport", back_populates="user", cascade="all, delete-orphan"
    )
    monthly_reports: Mapped[list["MonthlyReport"]] = relationship(
        "MonthlyReport", back_populates="user", cascade="all, delete-orphan"
    )
    xp_logs: Mapped[list["XpLog"]] = relationship(
        "XpLog", back_populates="user", cascade="all, delete-orphan"
    )
    media_progress: Mapped[list["MediaProgress"]] = relationship(
        "MediaProgress", back_populates="user", cascade="all, delete-orphan"
    )
    reminders: Mapped[list["Reminder"]] = relationship(
        "Reminder", back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )


class Level(Base):
    __tablename__ = "levels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    min_xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    order: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    users: Mapped[list["User"]] = relationship("User", back_populates="level")


class Goal(Base):
    __tablename__ = "goals"
    __table_args__ = (Index("ix_goals_user_type", "user_id", "goal_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    goal_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    current_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    unit: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="goals")


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_user_date", "user_id", "scheduled_date"),
        Index("ix_tasks_user_status", "user_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="tasks")
    history: Mapped[list["TaskHistory"]] = relationship(
        "TaskHistory", back_populates="task", cascade="all, delete-orphan"
    )


class TaskHistory(Base):
    __tablename__ = "task_history"
    __table_args__ = (Index("ix_task_history_task", "task_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    old_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    new_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    old_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    new_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task: Mapped["Task"] = relationship("Task", back_populates="history")


class Habit(Base):
    __tablename__ = "habits"
    __table_args__ = (Index("ix_habits_user_type", "user_id", "habit_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    habit_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="habits")
    logs: Mapped[list["HabitLog"]] = relationship(
        "HabitLog", back_populates="habit", cascade="all, delete-orphan"
    )


class HabitLog(Base):
    __tablename__ = "habit_logs"
    __table_args__ = (
        UniqueConstraint("habit_id", "log_date", name="uq_habit_log_date"),
        Index("ix_habit_logs_user_date", "user_id", "log_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    habit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    habit: Mapped["Habit"] = relationship("Habit", back_populates="logs")


class XpLog(Base):
    __tablename__ = "xp_logs"
    __table_args__ = (Index("ix_xp_logs_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="xp_logs")


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    icon: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    users: Mapped[list["UserAchievement"]] = relationship(
        "UserAchievement", back_populates="achievement"
    )


class UserAchievement(Base):
    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    achievement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False
    )
    unlocked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="achievements")
    achievement: Mapped["Achievement"] = relationship("Achievement", back_populates="users")


class DailyReport(Base):
    __tablename__ = "daily_reports"
    __table_args__ = (UniqueConstraint("user_id", "report_date", name="uq_daily_report"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    mood: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    productivity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    what_worked: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    what_blocked: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proud_of: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    day_index: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tasks_done: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tasks_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    coding_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    workout_done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    content_done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sleep_ok: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_rest_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    skipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="daily_reports")


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"
    __table_args__ = (
        UniqueConstraint("user_id", "week_start", name="uq_weekly_report"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    week_end: Mapped[date] = mapped_column(Date, nullable=False)
    tasks_completion_pct: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    coding_hours: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    games_hours: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    workouts_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    content_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    income_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    expense_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_day_index: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    analysis_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="weekly_reports")


class MonthlyReport(Base):
    __tablename__ = "monthly_reports"
    __table_args__ = (
        UniqueConstraint("user_id", "year", "month", name="uq_monthly_report"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tasks_completion_pct: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    coding_hours: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    workouts_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    income_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    expense_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    savings_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    weight_start: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weight_end: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="monthly_reports")


class FinanceCategory(Base):
    __tablename__ = "finance_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category_type: Mapped[str] = mapped_column(String(32), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    finances: Mapped[list["Finance"]] = relationship("Finance", back_populates="category")


class Finance(Base):
    __tablename__ = "finances"
    __table_args__ = (
        Index("ix_finances_user_date", "user_id", "occurred_at"),
        Index("ix_finances_user_type", "user_id", "finance_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("finance_categories.id", ondelete="SET NULL"), nullable=True
    )
    finance_type: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="finances")
    category: Mapped[Optional["FinanceCategory"]] = relationship(
        "FinanceCategory", back_populates="finances"
    )


class BodyProgress(Base):
    __tablename__ = "body_progress"
    __table_args__ = (Index("ix_body_progress_user_date", "user_id", "photo_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    photo_date: Mapped[date] = mapped_column(Date, nullable=False)
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="body_progress")


class WeightLog(Base):
    __tablename__ = "weight_logs"
    __table_args__ = (Index("ix_weight_logs_user_date", "user_id", "log_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="weight_logs")


class Workout(Base):
    __tablename__ = "workouts"
    __table_args__ = (Index("ix_workouts_user_date", "user_id", "workout_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Тренировка")
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    workout_type: Mapped[str] = mapped_column(String(64), nullable=False, default="strength")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    workout_date: Mapped[date] = mapped_column(Date, nullable=False)
    xp_earned: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="workouts")


class MediaProgress(Base):
    __tablename__ = "media_progress"
    __table_args__ = (Index("ix_media_progress_user_date", "user_id", "published_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(64), nullable=False, default="other")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    published_at: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="media_progress")


class UserSettings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    morning_time: Mapped[time] = mapped_column(Time, nullable=False, default=time(8, 0))
    evening_time: Mapped[time] = mapped_column(Time, nullable=False, default=time(21, 0))
    car_goal_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=Decimal("1500000")
    )
    relocation_goal_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=Decimal("300000")
    )
    daily_task_norm: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    target_weight: Mapped[float] = mapped_column(Float, nullable=False, default=75.0)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Europe/Moscow")
    motivation_images_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    new_year_ack_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    onboarding_done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    commands_pin_message_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    day_screen_message_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    north_star_goal: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="settings")


class Reminder(Base):
    __tablename__ = "reminders"
    __table_args__ = (Index("ix_reminders_user_active", "user_id", "is_active"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="reminders")


class RestDay(Base):
    __tablename__ = "rest_days"
    __table_args__ = (UniqueConstraint("user_id", "rest_date", name="uq_rest_day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rest_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="rest_days")


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    notification_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="notifications")


class Streak(Base):
    __tablename__ = "streaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_active_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="streak")
