"""rename total amount column

Revision ID: c4e9b0d4f1a2
Revises: 9f8c4d3b2a11
Create Date: 2026-03-19 00:00:01.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "c4e9b0d4f1a2"
down_revision = "9f8c4d3b2a11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Replace the old ore-based amount column with a plain total amount."""

    with op.batch_alter_table("booking_orders", schema=None) as batch_op:
        batch_op.add_column(sa.Column("total_amount", sa.Float(), nullable=True))

    op.execute("UPDATE booking_orders SET total_amount = total_amount_ore / 100.0")

    with op.batch_alter_table("booking_orders", schema=None) as batch_op:
        batch_op.alter_column(
            "total_amount",
            existing_type=sa.Float(),
            nullable=False,
        )
        batch_op.drop_column("total_amount_ore")


def downgrade() -> None:
    """Restore the older ore-based amount column."""

    with op.batch_alter_table("booking_orders", schema=None) as batch_op:
        batch_op.add_column(sa.Column("total_amount_ore", sa.Integer(), nullable=True))

    op.execute("UPDATE booking_orders SET total_amount_ore = CAST(total_amount * 100 AS INTEGER)")

    with op.batch_alter_table("booking_orders", schema=None) as batch_op:
        batch_op.alter_column(
            "total_amount_ore",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.drop_column("total_amount")
