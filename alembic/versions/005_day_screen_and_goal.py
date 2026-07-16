"""Add day_screen_message_id and north_star_goal to settings.

Revision ID: 005_day_screen_goal
Revises: 004_commands_pin
Create Date: 2026-07-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_day_screen_goal"
down_revision: Union[str, None] = "004_commands_pin"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "settings",
        sa.Column("day_screen_message_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "settings",
        sa.Column("north_star_goal", sa.String(length=120), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("settings", "north_star_goal")
    op.drop_column("settings", "day_screen_message_id")
