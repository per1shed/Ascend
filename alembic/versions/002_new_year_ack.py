"""Add new_year_ack_year to settings.

Revision ID: 002_new_year_ack
Revises: 001_initial
Create Date: 2026-07-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_new_year_ack"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "settings",
        sa.Column("new_year_ack_year", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("settings", "new_year_ack_year")
