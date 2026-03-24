"""add optional passenger fields to booked canoes

Revision ID: d5a4c2b1e8f7
Revises: b7f3c1d9e2a4
Create Date: 2026-03-24 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "d5a4c2b1e8f7"
down_revision = "b7f3c1d9e2a4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add optional second- and third-rider name fields to each canoe row."""

    op.add_column(
        "booked_canoes",
        sa.Column("passenger_two_first_name", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "booked_canoes",
        sa.Column("passenger_two_last_name", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "booked_canoes",
        sa.Column("passenger_three_first_name", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "booked_canoes",
        sa.Column("passenger_three_last_name", sa.String(length=120), nullable=True),
    )


def downgrade() -> None:
    """Remove the optional rider name fields from each canoe row."""

    op.drop_column("booked_canoes", "passenger_three_last_name")
    op.drop_column("booked_canoes", "passenger_three_first_name")
    op.drop_column("booked_canoes", "passenger_two_last_name")
    op.drop_column("booked_canoes", "passenger_two_first_name")
