"""Tests for Stripe configuration helpers."""

from types import SimpleNamespace

import pytest
import stripe

from app.util.stripe_helpers import (
    construct_stripe_webhook_event,
    create_stripe_checkout_session,
    expire_stripe_checkout_session,
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
        }
    )

    assert stripe_configuration.secret_key == "sk_test_123"
    assert stripe_configuration.webhook_secret == "whsec_123"
    assert stripe_configuration.public_base_url == "https://example.com"
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
            stripe_line_items=[{"quantity": 1}],
            metadata={"booking_order_id": "1"},
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
    assert captured_payload["expires_at"] is not None
    assert captured_payload["custom_text"] == {
        "submit": {
            "message": "Testläge: använd endast Stripe testkort under utveckling."
        }
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
