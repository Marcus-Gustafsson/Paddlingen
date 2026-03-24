"""Helpers for validating and preparing server-side checkout data.

This module keeps Stripe-ready booking and pricing logic outside the route
handlers. The current app still uses a simulated payment flow, but these
helpers let the backend prepare the exact server-approved booking data that a
later Stripe Checkout Session should use.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .db_models import Event
from .event_settings import normalize_money_decimal

CHECKOUT_CURRENCY = "sek"


@dataclass(frozen=True)
class PreparedCheckoutBooking:
    """Store the server-approved data for one checkout attempt.

    Attributes:
        active_event: Event row that owns the booking attempt.
        canoe_count: Number of canoes approved for this checkout.
        total_amount: Total amount in SEK stored on the local booking order.
        currency: Lowercase ISO currency code used both locally and for Stripe.
        stripe_line_items: Stripe-ready line-item data based only on server-side
            event settings.
    """

    active_event: Event
    canoe_count: int
    total_amount: Decimal
    currency: str
    stripe_line_items: list[dict[str, object]]


def convert_money_decimal_to_minor_units(amount: Decimal) -> int:
    """Convert a money value such as ``1200.00`` SEK into ore for Stripe.

    Args:
        amount: Money amount already normalized to two decimal places.

    Returns:
        int: Amount in the smallest currency unit used by Stripe.
    """

    normalized_amount = normalize_money_decimal(amount)
    return int(normalized_amount * 100)


def build_stripe_line_items_for_booking(
    active_event: Event,
    canoe_count: int,
) -> list[dict[str, object]]:
    """Build Stripe-ready line items from the server-side event settings.

    Args:
        active_event: Active event row that controls the booking price.
        canoe_count: Number of canoes approved by the server.

    Returns:
        list[dict[str, object]]: Stripe Checkout ``line_items`` data.
    """

    unit_price = normalize_money_decimal(active_event.price_per_canoe_sek)
    event_year = active_event.event_date.year

    return [
        {
            "price_data": {
                "currency": CHECKOUT_CURRENCY,
                "unit_amount": convert_money_decimal_to_minor_units(unit_price),
                "product_data": {
                    "name": f"Kanotbokning - {active_event.title}",
                    "description": (
                        f"Kanothyra för eventet {event_year}. Pris per kanot."
                    ),
                },
            },
            "quantity": canoe_count,
        }
    ]


def prepare_server_side_checkout_booking(
    active_event: Event,
    canoe_count: int,
) -> PreparedCheckoutBooking:
    """Build the server-approved booking and Stripe-ready checkout data.

    Args:
        active_event: Active event row that owns the booking.
        canoe_count: Number of canoes approved after validation.

    Returns:
        PreparedCheckoutBooking: Local order values plus Stripe-ready line-item
        data. This keeps later Checkout Session creation independent from any
        browser-sent price or amount field.
    """

    unit_price = normalize_money_decimal(active_event.price_per_canoe_sek)
    total_amount = normalize_money_decimal(unit_price * canoe_count)

    return PreparedCheckoutBooking(
        active_event=active_event,
        canoe_count=canoe_count,
        total_amount=total_amount,
        currency=CHECKOUT_CURRENCY,
        stripe_line_items=build_stripe_line_items_for_booking(
            active_event=active_event,
            canoe_count=canoe_count,
        ),
    )
