"""add event settings tables

Revision ID: 9f8c4d3b2a11
Revises: 63bd06093753
Create Date: 2026-03-19 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "9f8c4d3b2a11"
down_revision = "63bd06093753"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create event-setting tables and link bookings to events."""

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_date", sa.Date(), nullable=False, unique=True),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("subtitle", sa.String(length=255), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("starting_location_name", sa.String(length=255), nullable=False),
        sa.Column("starting_location_url", sa.String(length=500), nullable=False),
        sa.Column("end_location_name", sa.String(length=255), nullable=False),
        sa.Column("end_location_url", sa.String(length=500), nullable=False),
        sa.Column("available_canoes", sa.Integer(), nullable=False),
        sa.Column("price_per_canoe_sek", sa.Integer(), nullable=False),
        sa.Column("max_canoes_per_booking", sa.Integer(), nullable=False),
        sa.Column("weather_forecast_days_before_event", sa.Integer(), nullable=False),
        sa.Column("weather_latitude", sa.Float(), nullable=False),
        sa.Column("weather_longitude", sa.Float(), nullable=False),
        sa.Column("faq_booking_text", sa.Text(), nullable=False),
        sa.Column("faq_changes_and_questions_text", sa.Text(), nullable=False),
        sa.Column("rules_on_the_water_text", sa.Text(), nullable=False),
        sa.Column("rules_after_paddling_text", sa.Text(), nullable=False),
        sa.Column("contact_email", sa.String(length=255), nullable=False),
        sa.Column("contact_phone", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "event_weather_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("forecast_for_date", sa.Date(), nullable=False),
        sa.Column("summary", sa.String(length=255), nullable=True),
        sa.Column("temperature_c", sa.Float(), nullable=True),
        sa.Column("rain_mm", sa.Float(), nullable=True),
        sa.Column("icon", sa.String(length=32), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
    )

    with op.batch_alter_table("booking_orders", schema=None) as batch_op:
        batch_op.add_column(sa.Column("event_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_booking_orders_event_id", ["event_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_booking_orders_event_id_events",
            "events",
            ["event_id"],
            ["id"],
            ondelete="RESTRICT",
        )


def downgrade() -> None:
    """Remove the event-setting tables and the booking event link."""

    with op.batch_alter_table("booking_orders", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_booking_orders_event_id_events", type_="foreignkey"
        )
        batch_op.drop_index("ix_booking_orders_event_id")
        batch_op.drop_column("event_id")

    op.drop_table("event_weather_cache")
    op.drop_table("events")
