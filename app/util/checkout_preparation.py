"""Helpers for validating and preparing server-side checkout data.

This module keeps Stripe-ready booking and pricing logic outside the route
handlers. The current app still uses a simulated payment flow, but these
helpers let the backend prepare the exact server-approved booking data that a
later Stripe Checkout Session should use.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .db_models import Event
from .event_settings import format_swedish_date_display, normalize_money_decimal

CHECKOUT_CURRENCY = "sek"


def format_checkout_money_amount(amount: Decimal) -> str:
    """Return one short Swedish money label for hosted Checkout copy."""

    normalized_amount = normalize_money_decimal(amount)
    if normalized_amount == normalized_amount.to_integral():
        integer_amount = int(normalized_amount)
        return f"{integer_amount:,}".replace(",", " ") + " kr"

    amount_text = f"{normalized_amount:,.2f}"
    amount_text = amount_text.replace(",", " ").replace(".", ",")
    return f"{amount_text} kr"


def build_checkout_product_name(canoe_count: int) -> str:
    """Return the short hosted-Checkout product title for the booking."""

    if canoe_count == 1:
        return "1 kanot"

    return f"{canoe_count} kanoter"


def build_stripe_receipt_description(
    active_event: Event,
    canoe_count: int,
    public_booking_reference: str,
) -> str:
    """Build the short description Stripe shows in its payment receipt.

    Args:
        active_event: Event row that owns the booking.
        canoe_count: Number of canoes in the booking.
        public_booking_reference: Local booking reference shown to the visitor.

    Returns:
        str: Short Swedish receipt text suitable for Stripe's receipt
        description field.
    """

    event_date = active_event.event_date
    formatted_event_date = build_stripe_receipt_date_label(event_date)
    checkout_product_name = build_checkout_product_name(canoe_count)

    return (
        f"{active_event.title} - {checkout_product_name} - "
        f"{formatted_event_date} - Bokningsreferens {public_booking_reference}"
    )


def build_stripe_receipt_date_label(event_date: date) -> str:
    """Return one Swedish date label for Stripe receipt copy."""

    return format_swedish_date_display(event_date, include_year=True)


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
    unit_price_label = format_checkout_money_amount(unit_price)

    return [
        {
            "price_data": {
                "currency": CHECKOUT_CURRENCY,
                "unit_amount": convert_money_decimal_to_minor_units(unit_price),
                "product_data": {
                    "name": build_checkout_product_name(canoe_count),
                    "description": f"({unit_price_label} per kanot)",
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
