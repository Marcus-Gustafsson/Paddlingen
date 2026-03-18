"""initial booking schema

Revision ID: 63bd06093753
Revises:
Create Date: 2025-08-20 05:28:52.380050
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "63bd06093753"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the first normalized booking schema."""

    op.create_table(
        "booking_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "public_booking_reference", sa.String(length=40), nullable=False, unique=True
        ),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("canoe_count", sa.Integer(), nullable=False),
        sa.Column("total_amount_ore", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("payer_full_name", sa.String(length=120), nullable=True),
        sa.Column("payer_email", sa.String(length=255), nullable=True),
        sa.Column("payment_provider", sa.String(length=50), nullable=False),
        sa.Column("payment_provider_session_id", sa.String(length=255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=80), nullable=False, unique=True),
        sa.Column("pw_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "booked_canoes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("booking_order_id", sa.Integer(), nullable=False),
        sa.Column("participant_first_name", sa.String(length=120), nullable=False),
        sa.Column("participant_last_name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["booking_order_id"], ["booking_orders.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_booked_canoes_booking_order_id",
        "booked_canoes",
        ["booking_order_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the initial normalized booking schema."""

    op.drop_index("ix_booked_canoes_booking_order_id", table_name="booked_canoes")
    op.drop_table("booked_canoes")
    op.drop_table("admin_users")
    op.drop_table("booking_orders")
