"""Helpers for loading Stripe Checkout configuration safely.

This module keeps Stripe-related configuration in one place so later Checkout
and webhook steps can reuse the same validation rules instead of reading
environment variables directly in multiple routes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlsplit

from flask import current_app
import stripe


@dataclass(frozen=True)
class StripeCheckoutConfiguration:
    """Store the Stripe values needed for the first Checkout integration.

    Attributes:
        secret_key: Secret API key used by the backend to call Stripe.
        webhook_secret: Signing secret used later to verify Stripe webhooks.
        public_base_url: Root public URL used to build success and cancel
            return URLs.
    """

    secret_key: str
    webhook_secret: str
    public_base_url: str

    @property
    def success_url(self) -> str:
        """Return the Checkout success URL with Stripe's session placeholder."""

        return (
            f"{self.public_base_url}/payment-success"
            "?session_id={CHECKOUT_SESSION_ID}"
        )

    @property
    def cancel_url(self) -> str:
        """Return the Checkout cancel URL."""

        return f"{self.public_base_url}/payment-cancel"


def normalize_stripe_public_base_url(public_base_url: str) -> str:
    """Validate and normalize the configured public site base URL.

    Args:
        public_base_url: URL read from app configuration or the environment.

    Returns:
        The normalized root URL without a trailing slash.

    Raises:
        RuntimeError: If the URL is empty, not HTTP(S), or includes a path,
            query string, or fragment. For this project we want only the public
            site root, such as ``https://example.com``.
    """

    normalized_base_url = public_base_url.strip().rstrip("/")
    parsed_url = urlsplit(normalized_base_url)

    if not normalized_base_url:
        raise RuntimeError("STRIPE_PUBLIC_BASE_URL is missing.")

    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise RuntimeError(
            "STRIPE_PUBLIC_BASE_URL must start with http:// or https:// and "
            "include a hostname."
        )

    if parsed_url.path not in {"", "/"} or parsed_url.query or parsed_url.fragment:
        raise RuntimeError(
            "STRIPE_PUBLIC_BASE_URL must be only the site root, such as "
            "https://example.com."
        )

    return f"{parsed_url.scheme}://{parsed_url.netloc}"


def get_stripe_checkout_configuration_from_mapping(
    config_mapping: Mapping[str, Any],
) -> StripeCheckoutConfiguration:
    """Build validated Stripe Checkout configuration from a mapping.

    Args:
        config_mapping: Usually ``app.config`` or a test dictionary.

    Returns:
        A validated :class:`StripeCheckoutConfiguration` instance.

    Raises:
        RuntimeError: If one or more required values are missing or invalid.
    """

    secret_key = str(config_mapping.get("STRIPE_SECRET_KEY") or "").strip()
    webhook_secret = str(config_mapping.get("STRIPE_WEBHOOK_SECRET") or "").strip()
    public_base_url = str(config_mapping.get("STRIPE_PUBLIC_BASE_URL") or "").strip()

    missing_settings: list[str] = []
    if not secret_key:
        missing_settings.append("STRIPE_SECRET_KEY")
    if not webhook_secret:
        missing_settings.append("STRIPE_WEBHOOK_SECRET")
    if not public_base_url:
        missing_settings.append("STRIPE_PUBLIC_BASE_URL")

    if missing_settings:
        missing_values = ", ".join(missing_settings)
        raise RuntimeError(
            "Stripe Checkout is not configured. Missing required setting(s): "
            f"{missing_values}."
        )

    return StripeCheckoutConfiguration(
        secret_key=secret_key,
        webhook_secret=webhook_secret,
        public_base_url=normalize_stripe_public_base_url(public_base_url),
    )


def get_stripe_checkout_configuration() -> StripeCheckoutConfiguration:
    """Return validated Stripe Checkout configuration from the current app."""

    return get_stripe_checkout_configuration_from_mapping(current_app.config)


def is_stripe_checkout_configured() -> bool:
    """Return whether Stripe Checkout has all required configuration values."""

    try:
        get_stripe_checkout_configuration()
    except RuntimeError:
        return False
    return True


def build_stripe_client() -> stripe.StripeClient:
    """Return a Stripe client configured with the current app's secret key."""

    stripe_configuration = get_stripe_checkout_configuration()
    return stripe.StripeClient(stripe_configuration.secret_key)
