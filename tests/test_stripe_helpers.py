"""Tests for Stripe configuration helpers."""

import pytest

from app.util.stripe_helpers import (
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
        stripe_configuration.success_url
        == "https://example.com/payment-success?session_id={CHECKOUT_SESSION_ID}"
    )
    assert stripe_configuration.cancel_url == "https://example.com/payment-cancel"


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
        assert get_stripe_checkout_configuration().success_url.endswith(
            "{CHECKOUT_SESSION_ID}"
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
