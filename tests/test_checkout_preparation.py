"""Tests for server-side checkout preparation helpers."""

from datetime import date, time
from decimal import Decimal
from typing import cast

from app.util.checkout_preparation import (
    build_stripe_receipt_description,
    build_stripe_line_items_for_booking,
    convert_money_decimal_to_minor_units,
    prepare_server_side_checkout_booking,
)
from app.util.db_models import Event


def build_test_event(price_per_canoe_sek: Decimal) -> Event:
    """Return an in-memory event object for checkout helper tests."""

    return Event(
        title="Paddlingen",
        subtitle="Test",
        event_date=date(2026, 3, 20),
        start_time=time(10, 0),
        starting_location_name="Havsjomossen",
        starting_location_url="https://example.com/start",
        end_location_name="Havsjomossen",
        end_location_url="https://example.com/end",
        available_canoes=50,
        price_per_canoe_sek=price_per_canoe_sek,
        max_canoes_per_booking=5,
        weather_forecast_days_before_event=7,
        weather_latitude=59.86,
        weather_longitude=14.85,
        faq_booking_text="Booking info",
        faq_changes_and_questions_text="Change info",
        rules_on_the_water_text="Rules on the water",
        rules_after_paddling_text="Rules after paddling",
        contact_email="info@example.com",
        contact_phone="012-345 6789",
        is_active=True,
    )


def test_convert_money_decimal_to_minor_units_uses_ore() -> None:
    """Convert SEK values into the smallest Stripe currency unit."""

    assert convert_money_decimal_to_minor_units(Decimal("1200.00")) == 120000
    assert convert_money_decimal_to_minor_units(Decimal("1200.50")) == 120050


def test_build_stripe_line_items_for_booking_uses_server_event_price() -> None:
    """Build Stripe-ready line items from the event row instead of form data."""

    stripe_line_items = build_stripe_line_items_for_booking(
        active_event=build_test_event(Decimal("1500.00")),
        canoe_count=2,
    )

    assert stripe_line_items == [
        {
            "price_data": {
                "currency": "sek",
                "unit_amount": 150000,
                "product_data": {
                    "name": "2 kanoter",
                    "description": "(1 500 kr per kanot)",
                },
            },
            "quantity": 2,
        }
    ]


def test_build_stripe_receipt_description_uses_swedish_booking_summary() -> None:
    """Build one short Stripe receipt description from booking details."""

    receipt_description = build_stripe_receipt_description(
        active_event=build_test_event(Decimal("1200.00")),
        canoe_count=2,
        public_booking_reference="PAD-2026-00001",
    )

    assert receipt_description == (
        "Paddlingen - 2 kanoter - 20 mars 2026 - " "Bokningsreferens PAD-2026-00001"
    )


def test_prepare_server_side_checkout_booking_calculates_total_amount() -> None:
    """Calculate the local order total from the server-side event settings."""

    prepared_booking = prepare_server_side_checkout_booking(
        active_event=build_test_event(Decimal("1750.00")),
        canoe_count=3,
    )

    stripe_line_item = prepared_booking.stripe_line_items[0]
    price_data = cast(dict[str, object], stripe_line_item["price_data"])
    product_data = cast(dict[str, object], price_data["product_data"])

    assert prepared_booking.total_amount == Decimal("5250.00")
    assert prepared_booking.currency == "sek"
    assert stripe_line_item["quantity"] == 3
    assert product_data["name"] == "3 kanoter"
    assert product_data["description"] == "(1 750 kr per kanot)"
