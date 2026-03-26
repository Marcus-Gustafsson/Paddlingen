"""Tests for Stripe configuration helpers."""

from types import SimpleNamespace
from typing import cast

import pytest
import stripe

from app.util.stripe_helpers import (
    build_stripe_checkout_product_image_url,
    can_use_public_base_url_for_checkout_product_image,
    construct_stripe_webhook_event,
    create_stripe_checkout_session,
    enrich_checkout_line_items_for_hosted_checkout,
    expire_stripe_checkout_session,
    get_catalog_product_image_urls,
    get_stripe_checkout_configuration,
    get_stripe_checkout_configuration_from_mapping,
    is_stripe_checkout_configured,
    normalize_stripe_public_base_url,
)


def test_normalize_stripe_public_base_url_removes_trailing_slash() -> None:
    """Normalize a valid root URL so later Checkout links stay consistent."""

    assert (
        normalize_stripe_public_base_url("https://paddlingen.ngrok-free.app/")
        == "https://paddlingen.ngrok-free.app"
    )


def test_normalize_stripe_public_base_url_rejects_nested_paths() -> None:
    """Reject nested paths because this setting should point only to the site root."""

    with pytest.raises(RuntimeError, match="site root"):
        normalize_stripe_public_base_url("https://example.com/paddlingen")


def test_get_stripe_checkout_configuration_from_mapping_builds_return_urls() -> None:
    """Build the validated Stripe settings and derived return URLs."""

    stripe_configuration = get_stripe_checkout_configuration_from_mapping(
        {
            "STRIPE_SECRET_KEY": "sk_test_123",
            "STRIPE_WEBHOOK_SECRET": "whsec_123",
            "STRIPE_PUBLIC_BASE_URL": "https://example.com/",
            "STRIPE_CHECKOUT_PRODUCT_ID": "prod_123",
        }
    )

    assert stripe_configuration.secret_key == "sk_test_123"
    assert stripe_configuration.webhook_secret == "whsec_123"
    assert stripe_configuration.public_base_url == "https://example.com"
    assert stripe_configuration.checkout_product_id == "prod_123"
    assert (
        stripe_configuration.build_success_url("PAD-2026-00001")
        == "https://example.com/payment-success?order_ref=PAD-2026-00001&"
        "session_id={CHECKOUT_SESSION_ID}"
    )
    assert (
        stripe_configuration.build_cancel_url("PAD-2026-00001")
        == "https://example.com/payment-cancel?order_ref=PAD-2026-00001"
    )


def test_get_stripe_checkout_configuration_from_mapping_requires_all_values() -> None:
    """Raise a clear error message when Stripe config is incomplete."""

    with pytest.raises(
        RuntimeError,
        match=(
            "Missing required setting\\(s\\): STRIPE_SECRET_KEY, "
            "STRIPE_WEBHOOK_SECRET, STRIPE_PUBLIC_BASE_URL"
        ),
    ):
        get_stripe_checkout_configuration_from_mapping({})


def test_is_stripe_checkout_configured_returns_true_when_app_has_all_values(client):
    """Return True when the Flask app has the Stripe settings it needs."""

    with client.application.app_context():
        client.application.config.update(
            STRIPE_SECRET_KEY="sk_test_123",
            STRIPE_WEBHOOK_SECRET="whsec_123",
            STRIPE_PUBLIC_BASE_URL="https://example.com",
        )

        assert is_stripe_checkout_configured() is True
        assert (
            get_stripe_checkout_configuration()
            .build_success_url("PAD-2026-00001")
            .endswith("{CHECKOUT_SESSION_ID}")
        )
        assert (
            get_stripe_checkout_configuration()
            .build_cancel_url("PAD-2026-00001")
            .endswith("PAD-2026-00001")
        )


def test_is_stripe_checkout_configured_returns_false_when_values_are_missing(client):
    """Return False when any required Stripe value is still missing."""

    with client.application.app_context():
        client.application.config.update(
            STRIPE_SECRET_KEY="",
            STRIPE_WEBHOOK_SECRET="",
            STRIPE_PUBLIC_BASE_URL="",
        )

        assert is_stripe_checkout_configured() is False


def test_build_stripe_checkout_product_image_url_uses_public_base_url() -> None:
    """Build an absolute public URL for the hosted Checkout product image."""

    assert build_stripe_checkout_product_image_url("https://example.com") == (
        "https://example.com/static/images/canoe_checkout_icon_png.png"
    )


def test_can_use_public_base_url_for_checkout_product_image_rejects_localhost() -> None:
    """Reject localhost because Stripe cannot fetch hosted Checkout images there."""

    assert (
        can_use_public_base_url_for_checkout_product_image("http://127.0.0.1:5000")
        is False
    )
    assert can_use_public_base_url_for_checkout_product_image("https://example.com")


def test_get_catalog_product_image_urls_returns_dashboard_images() -> None:
    """Load product images from a real Stripe catalog product when configured."""

    fake_stripe_client = SimpleNamespace(
        v1=SimpleNamespace(
            products=SimpleNamespace(
                retrieve=lambda product_id: SimpleNamespace(
                    id=product_id,
                    images=["https://files.stripe.com/canoe.png"],
                )
            )
        )
    )

    assert get_catalog_product_image_urls(
        cast(stripe.StripeClient, fake_stripe_client),
        "prod_123",
    ) == ["https://files.stripe.com/canoe.png"]


def test_enrich_checkout_line_items_for_hosted_checkout_adds_product_image() -> None:
    """Add a public product image to hosted Checkout line items when missing."""

    line_items = [
        {
            "price_data": {
                "product_data": {
                    "name": "Kanotbokning - Paddlingen 2026",
                }
            },
            "quantity": 1,
        }
    ]

    enriched_line_items = enrich_checkout_line_items_for_hosted_checkout(
        line_items,
        ["https://example.com/static/images/canoe_checkout_icon_png.png"],
    )

    original_price_data = cast(dict[str, object], line_items[0]["price_data"])
    original_product_data = cast(dict[str, object], original_price_data["product_data"])
    enriched_price_data = cast(dict[str, object], enriched_line_items[0]["price_data"])
    enriched_product_data = cast(dict[str, object], enriched_price_data["product_data"])

    assert original_product_data.get("images") is None
    assert enriched_product_data["images"] == [
        "https://example.com/static/images/canoe_checkout_icon_png.png"
    ]


def test_create_stripe_checkout_session_uses_card_only_swedish_checkout(
    client, monkeypatch
) -> None:
    """Create sessions with Swedish locale and only card as payment method."""

    captured_payload: dict[str, object] = {}

    class FakeCheckoutSessionsApi:
        def create(self, payload: dict[str, object]) -> SimpleNamespace:
            captured_payload.update(payload)
            return SimpleNamespace(id="cs_test_123", url="https://checkout.stripe.test")

    fake_stripe_client = SimpleNamespace(
        v1=SimpleNamespace(
            checkout=SimpleNamespace(sessions=FakeCheckoutSessionsApi()),
        )
    )

    monkeypatch.setattr(
        "app.util.stripe_helpers.build_stripe_client",
        lambda: fake_stripe_client,
    )

    with client.application.app_context():
        create_stripe_checkout_session(
            public_booking_reference="PAD-2026-00001",
            stripe_line_items=[
                {
                    "quantity": 1,
                    "price_data": {
                        "product_data": {
                            "name": "2 kanoter",
                        }
                    },
                }
            ],
            metadata={"booking_order_id": "1"},
            payment_intent_description=(
                "Paddlingen - 2 kanoter - 20 mars 2026 - "
                "Bokningsreferens PAD-2026-00001"
            ),
        )

    assert captured_payload["locale"] == "sv"
    assert captured_payload["payment_method_types"] == ["card"]
    assert captured_payload["cancel_url"] == (
        "http://127.0.0.1:5000/payment-cancel?order_ref=PAD-2026-00001"
    )
    assert captured_payload["success_url"] == (
        "http://127.0.0.1:5000/payment-success?order_ref=PAD-2026-00001&"
        "session_id={CHECKOUT_SESSION_ID}"
    )
    assert captured_payload["submit_type"] == "book"
    assert captured_payload["payment_intent_data"] == {
        "description": (
            "Paddlingen - 2 kanoter - 20 mars 2026 - " "Bokningsreferens PAD-2026-00001"
        )
    }
    assert captured_payload["line_items"] == [
        {
            "quantity": 1,
            "price_data": {
                "product_data": {
                    "name": "2 kanoter",
                }
            },
        }
    ]
    assert captured_payload["expires_at"] is not None
    assert captured_payload["custom_text"] == {
        "submit": {
            "message": (
                "Reservationen blir bindande först när betalningen är slutförd."
            )
        },
        "after_submit": {
            "message": (
                "Du skickas tillbaka till Paddlingen direkt efter betalningen "
                "för bokningsbekräftelse och översikt."
            )
        },
    }


def test_create_stripe_checkout_session_uses_catalog_product_image_when_configured(
    client, monkeypatch
) -> None:
    """Prefer the Stripe Dashboard product image over the local fallback image."""

    captured_payload: dict[str, object] = {}

    class FakeCheckoutSessionsApi:
        def create(self, payload: dict[str, object]) -> SimpleNamespace:
            captured_payload.update(payload)
            return SimpleNamespace(id="cs_test_123", url="https://checkout.stripe.test")

    class FakeProductsApi:
        def retrieve(self, product_id: str) -> SimpleNamespace:
            assert product_id == "prod_checkout_123"
            return SimpleNamespace(
                id=product_id,
                images=["https://files.stripe.com/canoe-dashboard-image.png"],
            )

    fake_stripe_client = SimpleNamespace(
        v1=SimpleNamespace(
            checkout=SimpleNamespace(sessions=FakeCheckoutSessionsApi()),
            products=FakeProductsApi(),
        )
    )

    monkeypatch.setattr(
        "app.util.stripe_helpers.build_stripe_client",
        lambda: fake_stripe_client,
    )

    with client.application.app_context():
        client.application.config["STRIPE_CHECKOUT_PRODUCT_ID"] = "prod_checkout_123"
        create_stripe_checkout_session(
            public_booking_reference="PAD-2026-00001",
            stripe_line_items=[
                {
                    "quantity": 2,
                    "price_data": {
                        "product_data": {
                            "name": "2 kanoter",
                            "description": "(1 200 kr per kanot)",
                        }
                    },
                }
            ],
            metadata={"booking_order_id": "1"},
            payment_intent_description=(
                "Paddlingen - 2 kanoter - 20 mars 2026 - "
                "Bokningsreferens PAD-2026-00001"
            ),
        )

    assert captured_payload["line_items"] == [
        {
            "quantity": 2,
            "price_data": {
                "product_data": {
                    "name": "2 kanoter",
                    "description": "(1 200 kr per kanot)",
                    "images": ["https://files.stripe.com/canoe-dashboard-image.png"],
                }
            },
        }
    ]
    assert captured_payload["payment_intent_data"] == {
        "description": (
            "Paddlingen - 2 kanoter - 20 mars 2026 - " "Bokningsreferens PAD-2026-00001"
        )
    }


def test_expire_stripe_checkout_session_calls_stripe_expire_api(
    client, monkeypatch
) -> None:
    """Expire the open Stripe Checkout Session through Stripe's API."""

    captured_session_id: list[str] = []

    class FakeCheckoutSessionsApi:
        def expire(self, checkout_session_id: str) -> SimpleNamespace:
            captured_session_id.append(checkout_session_id)
            return SimpleNamespace(id=checkout_session_id, status="expired")

    fake_stripe_client = SimpleNamespace(
        v1=SimpleNamespace(
            checkout=SimpleNamespace(sessions=FakeCheckoutSessionsApi()),
        )
    )

    monkeypatch.setattr(
        "app.util.stripe_helpers.build_stripe_client",
        lambda: fake_stripe_client,
    )

    with client.application.app_context():
        expired_session = expire_stripe_checkout_session("cs_test_123")

    assert captured_session_id == ["cs_test_123"]
    assert expired_session.status == "expired"


def test_construct_stripe_webhook_event_uses_configured_webhook_secret(
    client, monkeypatch
) -> None:
    """Verify incoming webhook payloads with the configured signing secret."""

    captured_arguments: dict[str, object] = {}

    def fake_construct_event(*, payload, sig_header, secret):
        captured_arguments["payload"] = payload
        captured_arguments["sig_header"] = sig_header
        captured_arguments["secret"] = secret
        return {"id": "evt_test_123"}

    monkeypatch.setattr(stripe.Webhook, "construct_event", fake_construct_event)

    with client.application.app_context():
        stripe_event = construct_stripe_webhook_event(
            b'{"id":"evt_test_123"}',
            "t=123,v1=signature",
        )

    assert stripe_event == {"id": "evt_test_123"}
    assert captured_arguments == {
        "payload": b'{"id":"evt_test_123"}',
        "sig_header": "t=123,v1=signature",
        "secret": "whsec_test_123",
    }
