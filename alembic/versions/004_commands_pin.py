"""Add commands_pin_message_id to settings.

Revision ID: 004_commands_pin
Revises: 003_onboarding
Create Date: 2026-07-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_commands_pin"
down_revision: Union[str, None] = "003_onboarding"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "settings",
        sa.Column("commands_pin_message_id", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("settings", "commands_pin_message_id")
