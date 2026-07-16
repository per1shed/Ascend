"""Add onboarding_done to settings.

Revision ID: 003_onboarding
Revises: 002_new_year_ack
Create Date: 2026-07-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_onboarding"
down_revision: Union[str, None] = "002_new_year_ack"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "settings",
        sa.Column("onboarding_done", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    # новые пользователи получают False в коде при создании


def downgrade() -> None:
    op.drop_column("settings", "onboarding_done")
