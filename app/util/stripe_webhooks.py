"""Helpers for processing verified Stripe webhook events.

This module keeps webhook-related booking state changes outside the route layer
so the HTTP endpoint can stay small and the business rules can be tested more
directly.
"""

from __future__ import annotations

from collections.abc import Mapping

from flask import current_app

from .db_models import BookingOrder, db, get_current_utc_time

PENDING_WEBHOOK_BOOKING_ORDER_STATUSES = {
    "pending_payment",
    "checkout_session_created",
}


def get_stripe_object_value(stripe_object: object | None, key: str) -> object | None:
    """Return one value from either a mapping-like or attribute-like object."""

    if stripe_object is None:
        return None

    if isinstance(stripe_object, Mapping):
        return stripe_object.get(key)

    return getattr(stripe_object, key, None)


def get_checkout_session_from_event(stripe_event: object) -> object | None:
    """Return the Checkout Session object nested inside one Stripe event."""

    event_data = get_stripe_object_value(stripe_event, "data")
    return get_stripe_object_value(event_data, "object")


def get_checkout_session_metadata(checkout_session: object) -> dict[str, str]:
    """Return normalized metadata from one Checkout Session object."""

    raw_metadata = get_stripe_object_value(checkout_session, "metadata")
    if not isinstance(raw_metadata, Mapping):
        return {}

    return {str(key): str(value) for key, value in raw_metadata.items()}


def find_booking_order_for_checkout_session(
    checkout_session: object,
) -> BookingOrder | None:
    """Find the local booking order referenced by one Checkout Session."""

    metadata = get_checkout_session_metadata(checkout_session)
    booking_order_id_text = metadata.get("booking_order_id", "").strip()
    public_booking_reference = metadata.get("public_booking_reference", "").strip()
    checkout_session_id = str(
        get_stripe_object_value(checkout_session, "id") or ""
    ).strip()

    booking_order: BookingOrder | None = None
    if booking_order_id_text.isdigit():
        booking_order = db.session.get(BookingOrder, int(booking_order_id_text))

    if booking_order is None and public_booking_reference:
        booking_order = BookingOrder.query.filter_by(
            public_booking_reference=public_booking_reference
        ).first()

    if booking_order is None and checkout_session_id:
        booking_order = BookingOrder.query.filter_by(
            payment_provider_session_id=checkout_session_id
        ).first()

    return booking_order


def sync_payer_details_from_checkout_session(
    booking_order: BookingOrder,
    checkout_session: object,
) -> None:
    """Copy payer details from Stripe onto the local booking order when present."""

    customer_details = get_stripe_object_value(checkout_session, "customer_details")
    payer_email = str(
        get_stripe_object_value(customer_details, "email")
        or get_stripe_object_value(checkout_session, "customer_email")
        or ""
    ).strip()
    payer_full_name = str(
        get_stripe_object_value(customer_details, "name") or ""
    ).strip()

    if payer_email:
        booking_order.payer_email = payer_email

    if payer_full_name:
        booking_order.payer_full_name = payer_full_name


def confirm_paid_booking_from_checkout_session(checkout_session: object) -> str:
    """Mark a local booking as paid from a verified Checkout completion event."""

    checkout_session_id = str(
        get_stripe_object_value(checkout_session, "id") or ""
    ).strip()
    payment_status = str(
        get_stripe_object_value(checkout_session, "payment_status") or ""
    ).strip()

    if not checkout_session_id:
        current_app.logger.warning(
            "Ignored Stripe checkout completion because the session ID was missing."
        )
        return "ignored_missing_session_id"

    if payment_status != "paid":
        current_app.logger.warning(
            "Ignored Stripe checkout completion for %s because payment status was %s.",
            checkout_session_id,
            payment_status or "unknown",
        )
        return "ignored_unpaid_session"

    booking_order = find_booking_order_for_checkout_session(checkout_session)
    if booking_order is None:
        current_app.logger.warning(
            "Ignored Stripe checkout completion for %s because no local booking was found.",
            checkout_session_id,
        )
        return "ignored_missing_order"

    if booking_order.payment_provider_session_id != checkout_session_id:
        current_app.logger.warning(
            "Ignored Stripe checkout completion for booking %s because the stored "
            "session ID did not match.",
            booking_order.public_booking_reference,
        )
        return "ignored_session_mismatch"

    if booking_order.status == "paid":
        return "already_paid"

    if booking_order.status not in PENDING_WEBHOOK_BOOKING_ORDER_STATUSES:
        current_app.logger.warning(
            "Ignored Stripe checkout completion for booking %s because the local "
            "status was %s.",
            booking_order.public_booking_reference,
            booking_order.status,
        )
        return "ignored_not_pending"

    sync_payer_details_from_checkout_session(booking_order, checkout_session)
    booking_order.status = "paid"
    booking_order.paid_at = get_current_utc_time()
    booking_order.expires_at = None
    for booked_canoe in booking_order.booked_canoes:
        booked_canoe.status = "confirmed"

    db.session.commit()
    return "confirmed"


def release_expired_booking_from_checkout_session(checkout_session: object) -> str:
    """Release one unpaid booking after Stripe expires the Checkout Session."""

    checkout_session_id = str(
        get_stripe_object_value(checkout_session, "id") or ""
    ).strip()
    booking_order = find_booking_order_for_checkout_session(checkout_session)

    if booking_order is None:
        current_app.logger.info(
            "Ignored Stripe checkout expiration for %s because the local booking was already gone.",
            checkout_session_id or "unknown-session",
        )
        return "ignored_missing_order"

    if booking_order.payment_provider_session_id != checkout_session_id:
        current_app.logger.warning(
            "Ignored Stripe checkout expiration for booking %s because the stored "
            "session ID did not match.",
            booking_order.public_booking_reference,
        )
        return "ignored_session_mismatch"

    if booking_order.status == "paid":
        return "already_paid"

    if booking_order.status not in PENDING_WEBHOOK_BOOKING_ORDER_STATUSES:
        return "ignored_not_pending"

    db.session.delete(booking_order)
    db.session.commit()
    return "released"


def process_stripe_webhook_event(stripe_event: object) -> tuple[str, str]:
    """Apply one verified Stripe webhook event to local booking state."""

    event_type = str(get_stripe_object_value(stripe_event, "type") or "").strip()
    checkout_session = get_checkout_session_from_event(stripe_event)

    if event_type == "checkout.session.completed" and checkout_session is not None:
        return event_type, confirm_paid_booking_from_checkout_session(checkout_session)

    if event_type == "checkout.session.expired" and checkout_session is not None:
        return event_type, release_expired_booking_from_checkout_session(
            checkout_session
        )

    return event_type or "unknown", "ignored_unhandled_event"
