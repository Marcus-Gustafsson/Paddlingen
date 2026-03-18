"""Database models for bookings and administrator accounts.

This module keeps the SQLAlchemy model declarations separate from the Flask
application factory.  That makes the schema easier to reason about and easier
to reuse in tests, migrations, and helper scripts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from flask_login import UserMixin  # type: ignore[import-untyped]
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db: Any = SQLAlchemy()


def get_current_utc_time() -> datetime:
    """Return the current UTC time with timezone information.

    Returns:
        datetime: A timezone-aware UTC timestamp for audit columns.
    """

    return datetime.now(timezone.utc)


class BookingOrder(db.Model):
    """Store one booking or checkout attempt.

    Each row represents the parent order for one visitor action.  The related
    :class:`BookedCanoe` rows contain the individual participant names.
    """

    __tablename__ = "booking_orders"

    id = db.Column(db.Integer, primary_key=True)
    public_booking_reference = db.Column(db.String(40), unique=True, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="pending_payment")
    canoe_count = db.Column(db.Integer, nullable=False)
    total_amount_ore = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(10), nullable=False, default="sek")
    payer_full_name = db.Column(db.String(120), nullable=True)
    payer_email = db.Column(db.String(255), nullable=True)
    payment_provider = db.Column(db.String(50), nullable=False, default="simulated")
    payment_provider_session_id = db.Column(db.String(255), nullable=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    paid_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=get_current_utc_time
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=get_current_utc_time,
        onupdate=get_current_utc_time,
    )

    booked_canoes = db.relationship(
        "BookedCanoe",
        back_populates="booking_order",
        cascade="all, delete-orphan",
        order_by="BookedCanoe.id",
    )

    def __repr__(self) -> str:
        """Return a readable representation for debugging."""

        return (
            f"<BookingOrder id={self.id} ref={self.public_booking_reference} "
            f"status={self.status} canoe_count={self.canoe_count}>"
        )


class BookedCanoe(db.Model):
    """Store one participant name for one canoe booking."""

    __tablename__ = "booked_canoes"

    id = db.Column(db.Integer, primary_key=True)
    booking_order_id = db.Column(
        db.Integer, db.ForeignKey("booking_orders.id"), nullable=False, index=True
    )
    participant_first_name = db.Column(db.String(120), nullable=False)
    participant_last_name = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="reserved")
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=get_current_utc_time
    )

    booking_order = db.relationship("BookingOrder", back_populates="booked_canoes")

    @property
    def name(self) -> str:
        """Return the participant's full name for templates and admin forms."""

        full_name = (
            f"{self.participant_first_name} {self.participant_last_name}".strip()
        )
        return full_name or "Unnamed participant"

    @name.setter
    def name(self, full_name: str) -> None:
        """Split a full name string into first and last name fields.

        Args:
            full_name: Full name submitted from a simple admin form input.
        """

        cleaned_name = full_name.strip()
        if not cleaned_name:
            self.participant_first_name = "Unnamed"
            self.participant_last_name = "participant"
            return

        name_parts = cleaned_name.split(maxsplit=1)
        self.participant_first_name = name_parts[0]
        self.participant_last_name = name_parts[1] if len(name_parts) > 1 else ""

    def __repr__(self) -> str:
        """Return a readable representation for debugging."""

        return f"<BookedCanoe id={self.id} name={self.name} status={self.status}>"


class User(db.Model, UserMixin):
    """Store administrator login accounts for the protected admin area."""

    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    pw_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=get_current_utc_time
    )

    def set_password(self, password: str) -> None:
        """Hash and store an administrator password."""

        self.pw_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify a plaintext password against the stored password hash."""

        return check_password_hash(self.pw_hash, password)
