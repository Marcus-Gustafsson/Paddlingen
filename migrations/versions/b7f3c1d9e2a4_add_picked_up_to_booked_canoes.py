"""add picked_up column to booked canoes

Revision ID: b7f3c1d9e2a4
Revises: 2d3e4f5a6b7c
Create Date: 2026-03-23 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "b7f3c1d9e2a4"
down_revision = "2d3e4f5a6b7c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the event-day pickup flag to each booked canoe row."""

    op.add_column(
        "booked_canoes",
        sa.Column(
            "picked_up",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column("booked_canoes", "picked_up", server_default=None)


def downgrade() -> None:
    """Remove the event-day pickup flag from booked canoe rows."""

    op.drop_column("booked_canoes", "picked_up")
