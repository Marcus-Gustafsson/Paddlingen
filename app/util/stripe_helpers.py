"""Helpers for loading Stripe Checkout configuration safely.

This module keeps Stripe-related configuration in one place so later Checkout
and webhook steps can reuse the same validation rules instead of reading
environment variables directly in multiple routes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, cast
from urllib.parse import quote, urlsplit

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

    def build_success_url(self, booking_reference: str) -> str:
        """Return the Checkout success URL with order and session references.

        Args:
            booking_reference: Local public booking reference stored on the
                pending booking order.

        Returns:
            str: Success return URL that includes both the local booking
            reference and Stripe's session placeholder.
        """

        query_string = (
            f"order_ref={quote(booking_reference)}" "&session_id={CHECKOUT_SESSION_ID}"
        )
        return f"{self.public_base_url}/payment-success?{query_string}"

    def build_cancel_url(self, booking_reference: str) -> str:
        """Return the Checkout cancel URL for one local booking reference.

        Args:
            booking_reference: Local public booking reference stored on the
                pending booking order.

        Returns:
            str: Cancel return URL that lets the app identify which temporary
            order should be released.
        """

        query_string = f"order_ref={quote(booking_reference)}"
        return f"{self.public_base_url}/payment-cancel?{query_string}"


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


def create_stripe_checkout_session(
    public_booking_reference: str,
    stripe_line_items: list[dict[str, object]],
    metadata: Mapping[str, str],
) -> stripe.checkout.Session:
    """Create one hosted Stripe Checkout Session for a local booking attempt.

    Args:
        public_booking_reference: Local booking reference used in redirect URLs.
        stripe_line_items: Server-approved Stripe line items for the booking.
        metadata: Local identifiers stored on the Stripe session for later
            lookup and webhook handling.

    Returns:
        stripe.checkout.Session: Newly created Stripe Checkout Session.
    """

    stripe_configuration = get_stripe_checkout_configuration()
    stripe_client = build_stripe_client()

    return stripe_client.v1.checkout.sessions.create(
        {
            "mode": "payment",
            "locale": "sv",
            "payment_method_types": ["card"],
            "client_reference_id": public_booking_reference,
            "success_url": stripe_configuration.build_success_url(
                public_booking_reference
            ),
            "cancel_url": stripe_configuration.build_cancel_url(
                public_booking_reference
            ),
            "line_items": cast(Any, stripe_line_items),
            "metadata": dict(metadata),
            "custom_text": {
                "submit": {
                    "message": (
                        "Testläge: använd endast Stripe testkort under utveckling."
                    )
                }
            },
            # Stripe only allows expires_at between 30 minutes and 24 hours
            # from session creation. The local booking hold is shorter and is
            # enforced by the app before the visitor enters Stripe Checkout.
            "expires_at": int(
                (datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp()
            ),
        }
    )


def retrieve_stripe_checkout_session(
    checkout_session_id: str,
) -> stripe.checkout.Session:
    """Retrieve one Stripe Checkout Session by ID."""

    stripe_client = build_stripe_client()
    return stripe_client.v1.checkout.sessions.retrieve(checkout_session_id)


def expire_stripe_checkout_session(
    checkout_session_id: str,
) -> stripe.checkout.Session:
    """Expire one open Stripe Checkout Session by ID.

    Args:
        checkout_session_id: Stripe Checkout Session ID such as ``cs_test_...``.

    Returns:
        stripe.checkout.Session: Updated Checkout Session after Stripe expires
        it.
    """

    stripe_client = build_stripe_client()
    return stripe_client.v1.checkout.sessions.expire(checkout_session_id)


def construct_stripe_webhook_event(
    payload: bytes,
    stripe_signature_header: str,
) -> stripe.Event:
    """Verify and parse one incoming Stripe webhook event.

    Args:
        payload: Raw request body exactly as Flask received it.
        stripe_signature_header: Value from the incoming
            ``Stripe-Signature`` header.

    Returns:
        stripe.Event: Verified Stripe event object.

    Raises:
        ValueError: If the payload cannot be parsed as a Stripe event.
        stripe.SignatureVerificationError: If the signature does not match the
            configured webhook secret.
    """

    stripe_configuration = get_stripe_checkout_configuration()
    return stripe.Webhook.construct_event(
        payload=payload,
        sig_header=stripe_signature_header,
        secret=stripe_configuration.webhook_secret,
    )
