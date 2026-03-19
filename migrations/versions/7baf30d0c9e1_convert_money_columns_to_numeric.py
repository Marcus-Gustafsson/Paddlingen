"""convert money columns to numeric

Revision ID: 7baf30d0c9e1
Revises: c4e9b0d4f1a2
Create Date: 2026-03-19 00:00:02.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "7baf30d0c9e1"
down_revision = "c4e9b0d4f1a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Convert money columns to a shared fixed-point numeric type."""

    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.alter_column(
            "price_per_canoe_sek",
            existing_type=sa.Integer(),
            type_=sa.Numeric(10, 2),
            existing_nullable=False,
        )

    with op.batch_alter_table("booking_orders", schema=None) as batch_op:
        batch_op.alter_column(
            "total_amount",
            existing_type=sa.Float(),
            type_=sa.Numeric(10, 2),
            existing_nullable=False,
        )


def downgrade() -> None:
    """Restore the previous event-price and booking-total column types."""

    with op.batch_alter_table("booking_orders", schema=None) as batch_op:
        batch_op.alter_column(
            "total_amount",
            existing_type=sa.Numeric(10, 2),
            type_=sa.Float(),
            existing_nullable=False,
        )

    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.alter_column(
            "price_per_canoe_sek",
            existing_type=sa.Numeric(10, 2),
            type_=sa.Integer(),
            existing_nullable=False,
        )
